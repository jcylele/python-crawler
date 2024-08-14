import os.path
import shutil

from Consts import WorkerType, QueueType
from Ctrls import DbCtrl, ResCtrl, FileInfoCacheCtrl
from Models.BaseModel import ResState
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class ResValidWorker(BaseWorker):
    """
    worker to validate the size of temporary files
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.ResValid, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.ResValid

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        with DbCtrl.getSession() as dbSession, dbSession.begin():
            res2 = ResCtrl.getRes(dbSession, extra_info.res_id)
            tmp_file_path = res2.tmpFilePath()

            if os.path.exists(tmp_file_path):
                # check for file size
                real_size = os.path.getsize(tmp_file_path)
                if real_size < res2.res_size:
                    # delete invalid file
                    LogUtil.warn(f"{tmp_file_path} incorrect size, expect {res2.res_size:,d} get {real_size:,d}")
                    os.remove(tmp_file_path)

            if not os.path.exists(tmp_file_path):
                # throw back to file download queue
                QueueUtil.putbackResFile(self.QueueMgr(), item)
                return True

            # move to real location
            true_file_path = res2.filePath()
            try:
                shutil.move(tmp_file_path, true_file_path)
            except:
                return False
            res2.setState(ResState.Down)
            # refresh downloaded file size
            self.DownloadLimit().onDownloaded(res2.res_size)

            LogUtil.info(f"{true_file_path} saved")
            return True
