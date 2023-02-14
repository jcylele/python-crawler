import shutil

from Consts import WorkerType
from Ctrls import RequestCtrl
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class FileDownWorker(BaseWorker):
    """
    worker to download resource by url and save it to file
    """

    def __init__(self):
        super().__init__(worker_type=WorkerType.FileDown)
        self.requestSession = RequestCtrl.createRequestSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.FileDownload

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        self.requestSession.headers["referer"] = item.from_url
        with self.requestSession.get(item.url, stream=True) as r:
            with open(extra_info.file_path, 'wb') as f:
                # write stream data into file, the most efficient way of download that I know
                shutil.copyfileobj(r.raw, f)

        # enqueue for validation
        QueueUtil.enqueueResValid(item)

        return True
