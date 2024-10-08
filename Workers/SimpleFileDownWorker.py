import os

from Consts import WorkerType, QueueType
from Utils import LogUtil
from WorkQueue.ExtraInfo import FilePathExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker


class SimpleFileDownWorker(BaseRequestWorker):
    """
    worker to download small images
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.SimpleFile, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.SimpleFile

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: FilePathExtraInfo = item.extra_info
        file_path = extra_info.file_path
        # double check file exists
        if os.path.exists(file_path):
            return True
        succeed, size = self._head(item)
        if not succeed:
            LogUtil.warn(f"head failed: {item.url}")
            return False
        self._downloadStream(item.url, file_path)

        real_size = os.path.getsize(file_path)
        if real_size != size:
            # delete invalid file
            LogUtil.warn(f"{file_path} incorrect size, expect {size:,d} get {real_size:,d}")
            os.remove(file_path)
            return False

        return True
