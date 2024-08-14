import os.path
import time

import Configs
from Consts import WorkerType, QueueType
from Download import FileManager
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker

# resume uncompleted files which are large enough
# in case that the content is just error msg
MinResumeSize = 1024 * 1024


class FileDownWorker(BaseRequestWorker):
    """
    worker to download resource by url and save it to file
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FileDown, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FileDownload

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        self.requestSession.headers["referer"] = item.from_url

        # protection
        while not FileManager.useFile(extra_info.file_path, self.native_id):
            self._sleep()

        # check for total file size, skip if not enough
        if not self.DownloadLimit().canDownload(extra_info.file_size):
            return True

        file_mode = "wb"
        file_path = extra_info.file_path
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            # rarely, but possible
            if file_size == extra_info.file_size:
                QueueUtil.enqueueResValid(self.QueueMgr(), item)
                FileManager.releaseFile(file_path, self.native_id)
                return True
            # if there is an uncompleted file and its size is large enough
            # resume the download instead of starting from the beginning
            if file_size >= MinResumeSize:
                file_mode = "ab"
                self.requestSession.headers["Range"] = f"bytes={file_size}-"
                # for test, change to debug after that
                LogUtil.warn(f"resume {file_path} from {file_size:,d}")

        # if timeout, start a new thread to download other files
        self.setTimeout(Configs.BASE_TIME_OUT + extra_info.file_size / Configs.MIN_DOWN_SPEED)

        self._downloadStream(item.url, file_path, file_mode)

        # remove the range attribute in header
        if "Range" in self.requestSession.headers:
            self.requestSession.headers.pop("Range")
        # enqueue for validation
        QueueUtil.enqueueResValid(self.QueueMgr(), item)
        FileManager.releaseFile(file_path, self.native_id)

        return True
