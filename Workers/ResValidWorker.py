import os.path

import Consts
import LogUtil
from Ctrls import CtrlUtil, ResCtrl
from Models.BaseModel import ResState
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class ResValidWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type=Consts.WorkerType.ResValid)
        self.session = Consts.createSession()

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.ResValid

    def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        with CtrlUtil.getSession() as session2, session2.begin():
            res2 = ResCtrl.getRes(session2, extra_info.res_id)
            tmp_file_path = res2.tmpFilePath()

            if os.path.exists(tmp_file_path):
                real_size = os.path.getsize(tmp_file_path)
                if real_size < res2.res_size:
                    LogUtil.warn(f"{tmp_file_path} incorrect size, expect {res2.res_size:,d} get {real_size:,d}")
                    os.remove(tmp_file_path)

            if not os.path.exists(tmp_file_path):
                # 重新丢到ResFile去
                QueueUtil.enqueueResFile(item, extra_info.file_path, res2.res_size)
                return True

            # 验证通过
            true_file_path = res2.filePath()
            os.rename(tmp_file_path, true_file_path)
            res2.res_state = ResState.Down

            LogUtil.info(f"{true_file_path} saved")
            return True



