import os.path
import shutil

from sqlalchemy import func
from sqlalchemy.orm import Session

from Consts import WorkerType, QueueType, ResState
from Ctrls import ActorCtrl, ActorFileCtrl, DbCtrl, ResCtrl, ResFileCtrl
from Utils import LogUtil
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

    @staticmethod
    def updateLastResDownloadTime(session: Session, actor_id: int):
        actor = ActorCtrl.getActor(session, actor_id)
        actor.last_res_download_time = func.now()

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
                    LogUtil.warn(
                        f"{tmp_file_path} incorrect size, expect {res2.res_size:,d} get {real_size:,d}")
                    os.remove(tmp_file_path)

            if not os.path.exists(tmp_file_path):
                # throw back to file download queue
                self.QueueMgr().putbackResFile(item)
                return True

            # move to real location
            true_file_path = res2.filePath()
            try:
                shutil.move(tmp_file_path, true_file_path)
            except:
                return False

            # get media info
            width, height, duration = ResFileCtrl.get_media_info(
                true_file_path)
            if width > 0 and height > 0:
                res2.res_width = width
                res2.res_height = height
                if duration > 0:
                    res2.res_duration = duration

            res2.setState(ResState.Down)
            # refresh downloaded file size
            self.DownloadLimit().onDownloaded(res2.res_size)
            ResValidWorker.updateLastResDownloadTime(
                dbSession, extra_info.actor_info.actor_id)
            LogUtil.info(f"{true_file_path} saved")
            return True
