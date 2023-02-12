import time

import Consts
import LogUtil
from WorkQueue import QueueMgr
from WorkQueue.PageQueueItem import PageQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class PageDownWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type=Consts.WorkerType.PageDown)
        self.session = Consts.createSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.Download

    def _process(self, item: UrlQueueItem) -> bool:
        content = self.__download(item)
        if content is not None:
            out_item = PageQueueItem(item.url, content, item.extra_info)
            QueueMgr.add(item.extra_info.queueType(), out_item)
            return True
        else:
            LogUtil.warn(f"download failed: {item.url} ")
            # 失败之后换个session
            self.session = Consts.createSession()
            return False

    def __download(self, item: UrlQueueItem) -> str:
        # time.sleep(1.0)
        self.session.headers["referer"] = item.from_url
        try:
            res = self.session.get(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return None

        if res.status_code == 200:
            return res.text
        elif res.status_code == 302:
            item.from_url = item.url
            item.url = res.headers['Location']
            return self.__download(item)
        elif res.status_code == 429:
            time.sleep(5)
            LogUtil.warn(f"get {item.extra_info} too fast")
            return self.__download(item)
        else:
            LogUtil.info(f"get error {res.status_code}: {item.url}")
            return None
