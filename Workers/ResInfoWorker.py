from Consts import WorkerType, QueueType
from Ctrls import DbCtrl, ResCtrl
from Models.BaseModel import ResState, ResModel
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.ExtraInfo import ResInfoExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker


class ResInfoWorker(BaseRequestWorker):
    """
    worker to get the size of a resource from the header
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.ResInfo, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.ResInfo

    def _process(self, item: UrlQueueItem) -> bool:
        succeed, size = self._head(item)
        if not succeed:
            LogUtil.warn(f"head failed: {item.url}")
            return False

        # keep session life short, no time-consuming things allowed
        # so head first, then start session
        with DbCtrl.getSession() as session1, session1.begin():
            extra_info: ResInfoExtraInfo = item.extra_info
            res1: ResModel = ResCtrl.getRes(session1, extra_info.res_id)
            if res1 is None:
                LogUtil.warn(f"res not found {extra_info}")
                return False

            res1.setSize(size)
            max_file_size = self.DownloadLimit().file_size
            # skip files which are too large for now
            if size > max_file_size > 0:
                res1.setState(ResState.Skip)
                LogUtil.info(f"{extra_info} too big: {size:,d}")
                return True

            # enqueue for downloading
            QueueUtil.enqueueResFile(self.QueueMgr(), item, res1.tmpFilePath(), size)

            return True
