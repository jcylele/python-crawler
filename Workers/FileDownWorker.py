import os.path

import Configs
from Consts import WorkerType, QueueType
from Ctrls import DbCtrl
from Download import FileManager
from Utils import LogUtil
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

        # skip if no folder
        with DbCtrl.getSession() as session, session.begin():
            if not self.hasActorFolder(session, extra_info.actor_info.actor_id):
                return True

        self.requestSession.headers["referer"] = item.from_url

        # protection, skip if other thread is downloading
        while not FileManager.useFile(extra_info.file_path, self.native_id):
            return True

        # check for total file size, skip if not enough
        if not self.DownloadLimit().canDownload(extra_info.file_size):
            FileManager.releaseFile(extra_info.file_path, self.native_id)
            return True

        file_mode = "wb"
        file_path = extra_info.file_path
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            # rarely, but possible
            if file_size == extra_info.file_size:
                FileManager.releaseFile(file_path, self.native_id)
                self.QueueMgr().enqueueResValid(item)
                return True
            # if there is an uncompleted file and its size is large enough
            # resume the download instead of starting from the beginning
            if file_size >= MinResumeSize:
                file_mode = "ab"
                self.requestSession.headers["Range"] = f"bytes={file_size}-"
                # for test, change to debug after that
                LogUtil.warn(f"resume {file_path} from {file_size:,d}")

        # if timeout, start a new thread to download other files
        self.setTimeout(Configs.BASE_TIME_OUT +
                        extra_info.file_size / Configs.MIN_DOWN_SPEED)

        self._downloadStream(item.url, file_path, file_mode)

        # remove the range attribute in header
        if "Range" in self.requestSession.headers:
            self.requestSession.headers.pop("Range")

        FileManager.releaseFile(file_path, self.native_id)
        # enqueue for validation
        self.QueueMgr().enqueueResValid(item)

        return True
