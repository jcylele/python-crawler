import os.path

import aiofiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from Consts import WorkerType, QueueType, ResState
from Ctrls import ActorCtrl, DbCtrl, ResCtrl
from Utils import LogUtil, PyUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class ResValidWorker(BaseWorker):
    """
    worker to validate the size of temporary files
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.ResValid, task=task)

    @staticmethod
    def updateLastResDownloadTime(session: Session, actor_id: int):
        actor = ActorCtrl.getActor(session, actor_id)
        actor.last_res_download_time = func.now()

    async def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info

        with DbCtrl.getSession() as dbSession, dbSession.begin():
            res1 = ResCtrl.getRes(dbSession, extra_info.res_id)
            tmp_file_path = res1.tmpFilePath()
            true_file_path = res1.filePath()
            true_size = res1.res_size

        if os.path.exists(tmp_file_path):
            # check for file size
            real_size = os.path.getsize(tmp_file_path)
            if real_size < true_size:
                # delete invalid file
                LogUtil.warning(
                    f"{tmp_file_path} incorrect size, expect {true_size:,d} get {real_size:,d}")
                os.remove(tmp_file_path)

        if not os.path.exists(tmp_file_path):
            # throw back to file download queue
            await self.queue_mgr().requeueItem(QueueType.FileDownload, item)
            return True

        # move to real location
        try:
            await aiofiles.os.rename(tmp_file_path, true_file_path)
        except FileExistsError as e:
            # rare case, remove the temporary file
            await aiofiles.os.remove(tmp_file_path)
        except Exception as e:
            LogUtil.exception(e)
            return False

        # get media info
        width, height, duration = PyUtil.get_media_info(
            true_file_path)

        # update db
        with DbCtrl.getSession() as dbSession, dbSession.begin():
            res2 = ResCtrl.getRes(dbSession, extra_info.res_id)
            if width > 0 and height > 0:
                res2.res_width = width
                res2.res_height = height
                if duration > 0:
                    res2.res_duration = duration

            res2.setState(ResState.Down)
            ResValidWorker.updateLastResDownloadTime(
                dbSession, extra_info.actor_info.actor_id)

        # refresh downloaded progress
        self.DownloadLimit().onDownloaded(true_size)
        LogUtil.info(f"{true_file_path} saved")
        return True
