import time

import Configs
from Consts import WorkerType
from Utils import LogUtil
from Ctrls import DbCtrl, ResCtrl, RequestCtrl
from Models.BaseModel import ResState, ResModel
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResInfoExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class ResInfoWorker(BaseWorker):
    """
    worker to get the size of a resource from the header
    """

    def __init__(self):
        super().__init__(worker_type=WorkerType.ResInfo)
        self.requestSession = RequestCtrl.createRequestSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.ResInfo

    def _process(self, item: UrlQueueItem) -> bool:
        succeed, size = self.__head(item)
        if not succeed:
            LogUtil.warn(f"head failed: {item.url}")
            return False

        # keep session life short, no time-consuming things allowed
        # so head first, then start session
        with DbCtrl.getSession() as session1, session1.begin():
            extra_info: ResInfoExtraInfo = item.extra_info
            res1: ResModel = ResCtrl.getRes(session1, extra_info.res_id)
            if res1 is None:
                LogUtil.warn(f"res not found {extra_info}")
                return False

            res1.res_size = size
            # skip files which are too large for now
            if size > Configs.MaxFileSize:
                res1.res_state = ResState.Skip
                LogUtil.info(f"{extra_info} too big: {size:,d}")
                return True

            # enqueue for downloading
            QueueUtil.enqueueResFile(item, res1.tmpFilePath(), size)

            return True

    def __head(self, item: UrlQueueItem) -> (bool, int):
        """
        get size of a web resource
        :return (succeed or not, size of the resource)
        """
        # time.sleep(1.0)
        # set the last url, some websites check for it
        self.requestSession.headers["referer"] = item.from_url
        try:
            res = self.requestSession.head(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return False, 0

        if res.status_code == 200:
            content_length = res.headers.get('Content-Length')
            if content_length is None:
                return True, 0
            return True, int(content_length)
        elif res.status_code == 302:  # redirect
            item.from_url = item.url
            item.url = res.headers['Location']
            return self.__head(item)
        elif res.status_code == 429:  # too fast
            time.sleep(5)
            LogUtil.warn(f"head {item.extra_info} too fast")
            return self.__head(item)
        else:
            LogUtil.info(f"head error {res.status_code}: {item.url}")
            return False, 0
