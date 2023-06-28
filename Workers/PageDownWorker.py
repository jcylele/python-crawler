from Consts import WorkerType, QueueType
from Utils import LogUtil
from WorkQueue.PageQueueItem import PageQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker


class PageDownWorker(BaseRequestWorker):
    """
    worker to download a web page
    """
    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.PageDown, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.PageDownload

    def _process(self, item: UrlQueueItem) -> bool:
        content = self._download(item)
        if content is not None:
            out_item = PageQueueItem(item.url, content, item.extra_info)
            # enqueue according to the extra_info
            self.QueueMgr().put(item.extra_info.queueType(), out_item)
            return True
        else:
            LogUtil.warn(f"download failed: {item.url} ")
            return False


