import shutil

import Consts
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class FileDownWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type=Consts.WorkerType.FileDown)
        self.session = Consts.createSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.ResFile

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        self.session.headers["referer"] = item.from_url
        with self.session.get(item.url, stream=True) as r:
            with open(extra_info.file_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        QueueUtil.enqueueResValid(item)
        return True
