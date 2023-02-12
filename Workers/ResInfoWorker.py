import time

import Configs
import Consts
import LogUtil
from Ctrls import CtrlUtil, ResCtrl
from Models.BaseModel import ResState, ResModel
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class ResInfoWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type=Consts.WorkerType.ResInfo)
        self.session = Consts.createSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.ResInfo

    def _process(self, item: UrlQueueItem) -> bool:
        succeed, size = self.__head(item)
        if not succeed:
            LogUtil.warn(f"head failed: {item.url}")
            # 失败之后换个session
            self.session = Consts.createSession()
            return False

        with CtrlUtil.getSession() as session1, session1.begin():
            extra_info: ResExtraInfo = item.extra_info
            res1: ResModel = ResCtrl.getRes(session1, extra_info.res_id)
            if res1 is None:
                LogUtil.warn(f"res not found {extra_info}")
                return False

            res1.res_size = size
            if size > Configs.MaxFileSize:
                res1.res_state = ResState.Skip
                LogUtil.info(f"{extra_info} too big: {size:,d}")
                return True

            QueueUtil.enqueueResFile(item, res1.tmpFilePath(), size)
            return True

    def __head(self, item: UrlQueueItem):
        # time.sleep(1.0)
        self.session.headers["referer"] = item.from_url
        try:
            res = self.session.head(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return False, 0

        if res.status_code == 200:
            content_length = res.headers.get('Content-Length')
            if content_length is None:
                return True, 0
            return True, int(content_length)
        elif res.status_code == 302:
            item.from_url = item.url
            item.url = res.headers['Location']
            return self.__head(item)
        elif res.status_code == 429:
            time.sleep(5)
            LogUtil.warn(f"head {item.extra_info} too fast")
            return self.__head(item)
        else:
            LogUtil.info(f"head error {res.status_code}: {item.url}")
            return False, 0
