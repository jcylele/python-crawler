import time

from Consts import WorkerType
from Utils import LogUtil
from Ctrls import RequestCtrl
from WorkQueue import QueueMgr
from WorkQueue.PageQueueItem import PageQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class PageDownWorker(BaseWorker):
    """
    worker to download a web page
    """

    def __init__(self):
        super().__init__(worker_type=WorkerType.PageDown)
        self.requestSession = RequestCtrl.createRequestSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.PageDownload

    def _process(self, item: UrlQueueItem) -> bool:
        content = self.__download(item)
        if content is not None:
            out_item = PageQueueItem(item.url, content, item.extra_info)
            # enqueue according to the extra_info
            QueueMgr.put(item.extra_info.queueType(), out_item)
            return True
        else:
            LogUtil.warn(f"download failed: {item.url} ")
            return False

    def __download(self, item: UrlQueueItem) -> str:
        """
        download the web page
        """

        # time.sleep(1.0)
        # set the last url, some websites check for it
        self.requestSession.headers["referer"] = item.from_url
        try:
            res = self.requestSession.get(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return None

        if res.status_code == 200:
            return res.text
        elif res.status_code == 302:  # redirect
            item.from_url = item.url
            item.url = res.headers['Location']
            return self.__download(item)
        elif res.status_code == 429:  # too fast
            time.sleep(5)
            LogUtil.warn(f"get {item.extra_info} too fast")
            return self.__download(item)
        else:
            LogUtil.info(f"get error {res.status_code}: {item.url}")
            return None
