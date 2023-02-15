import os.path
import shutil

from Consts import WorkerType
from Ctrls import RequestCtrl
from Utils import LogUtil
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker

# resume uncompleted files which are large enough
# in case that the content is just error msg
MinResumeSize = 1024 * 1024


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

        file_mode = "wb"
        file_path = extra_info.file_path
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            # rarely, but possible
            if file_size == extra_info.file_size:
                QueueUtil.enqueueResValid(item)
                return True
            # if there is an uncompleted file and its size is large enough
            # resume the download instead of starting from the beginning
            if file_size >= MinResumeSize:
                file_mode = "ab"
                self.requestSession.headers["Range"] = f"bytes={file_size}-"
                # for test, change to debug after that
                LogUtil.warn(f"resume {file_path} from {file_size:,d}")

        with self.requestSession.get(item.url, stream=True) as r:
            with open(file_path, file_mode) as f:
                # write stream data into file, the most efficient way of download that I know
                shutil.copyfileobj(r.raw, f)

        # remove the range attribute in header
        if "Range" in self.requestSession.headers:
            self.requestSession.headers.pop("Range")
        # enqueue for validation
        QueueUtil.enqueueResValid(item)

        return True
