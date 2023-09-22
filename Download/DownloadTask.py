import os

import Configs
import Consts
from Ctrls import DbCtrl, ActorCtrl, ResCtrl
from Download.DownloadLimit import DownloadLimit
from Guarder import Guarder
from Models.BaseModel import ActorCategory
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.QueueMgr import QueueMgr
from Workers import WorkerMgr


class DownloadTask(object):
    def __init__(self, task_uid):
        self.uid = task_uid
        self.guarder = Guarder(self)
        self.queueMgr = QueueMgr()
        self.downloadLimit: DownloadLimit = None
        self.desc = ""
        self.worker_count = {}

    def getWorkerCount(self, work_type: Consts.WorkerType) -> int:
        if work_type in self.worker_count:
            return self.worker_count[work_type]
        return WorkerMgr.getWorkerCount(work_type)

    def startDownload(self):
        """
        new all threads and start running
        :return:
        """
        for work_type in Consts.WorkerType:
            count = self.getWorkerCount(work_type)
            for i in range(count):
                worker = WorkerMgr.createWorker(work_type, self)
                self.guarder.addWorker(worker)
        self.guarder.start()

    def Stop(self):
        self.guarder.Stop()

    def isDone(self) -> bool:
        return self.guarder.done

    def setLimit(self, limit: DownloadLimit):
        """
        set download limit
        """
        self.downloadLimit = limit

    def downloadNewActors(self):
        """
        download new actors
        """
        self.desc = "New Actors."
        QueueUtil.enqueueFetchActors(self.queueMgr)
        self.startDownload()

    def downloadByActorCategory(self, actor_category: ActorCategory):
        """
        download actors in corresponding category
        """
        self.desc = f"Actors in {actor_category}."
        self.worker_count[Consts.WorkerType.FetchActors] = 0
        with DbCtrl.getSession() as session, session.begin():
            actors = ActorCtrl.getActorsByCategory(session, actor_category)
            for actor in actors:
                QueueUtil.enqueueFetchActor(self.queueMgr, actor.actor_name)
        self.startDownload()

    def downloadSpecificActors(self, actor_names: list[str]):
        """
        download specific actors
        """
        self.desc = f"Specific Actors {','.join(actor_names)}."
        self.worker_count[Consts.WorkerType.FetchActors] = 0
        val = WorkerMgr.getWorkerCount(Consts.WorkerType.FetchActor)
        val = min(val, len(actor_names))
        self.worker_count[Consts.WorkerType.FetchActor] = val
        for actor_name in actor_names:
            QueueUtil.enqueueFetchActor(self.queueMgr, actor_name)
        self.startDownload()

    @staticmethod
    def initEnv():
        """
        initialize the environment
        :return:
        """
        LogUtil.info("initializing environment...")
        os.makedirs(Configs.RootFolder, exist_ok=True)
        os.makedirs(Configs.formatTmpFolderPath(), exist_ok=True)
        os.makedirs(Configs.formatIconFolderPath(), exist_ok=True)
        DbCtrl.init()
        # repairRecords()

    @staticmethod
    def repairRecords():
        """
        refresh database according to the existence of files and folders
        :return:
        """
        with DbCtrl.getSession() as session, session.begin():
            ActorCtrl.repairRecords(session)
        with DbCtrl.getSession() as session, session.begin():
            ResCtrl.repairRecords(session)

    def __repr__(self):
        return f"({self.desc}\tdownloadLimit={self.downloadLimit}"

    def toJson(self):
        return {'uid': self.uid, 'desc': self.desc, 'downloadLimit': self.downloadLimit.toJson()}
