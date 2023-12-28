import os

import Configs
import Consts
from Ctrls import DbCtrl, ActorCtrl, ResCtrl
from Download.DownloadLimit import DownloadLimit
from Guarder import Guarder
from Models.ActorInfo import ActorInfo
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
        LogUtil.setMinLogLv(LogUtil.LogLv.Info)
        for work_type in Consts.WorkerType:
            count = self.getWorkerCount(work_type)
            for i in range(count):
                worker = WorkerMgr.createWorker(work_type, self)
                self.guarder.addWorker(worker)
        self.guarder.start()

    def Stop(self):
        self.guarder.Stop()
        self.queueMgr.clear()

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
            actor_count = 0
            for actor in actors:
                QueueUtil.enqueueFetchActor(self.queueMgr, actor.actor_name)
                actor_count += 1
            self.worker_count[Consts.WorkerType.FetchActor] = min(actor_count, Configs.MAX_DOWN_WORKER_COUNT)
        self.startDownload()

    def downloadSpecificActors(self, actor_names: list[str]):
        """
        download specific actors
        """
        self.desc = f"Specific Actors {','.join(actor_names)}."
        self.worker_count[Consts.WorkerType.FetchActors] = 0
        val = WorkerMgr.getWorkerCount(Consts.WorkerType.FetchActor)
        val = min(val, len(actor_names), Configs.MAX_DOWN_WORKER_COUNT)
        self.worker_count[Consts.WorkerType.FetchActor] = val
        for actor_name in actor_names:
            QueueUtil.enqueueFetchActor(self.queueMgr, actor_name)
        self.startDownload()

    def downloadAllPosts(self, actor_name: str):
        """
        download all posts of an actor
        """
        self.desc = f"All posts of {actor_name}."
        self.worker_count[Consts.WorkerType.FetchActors] = 0
        self.worker_count[Consts.WorkerType.FetchActor] = 0
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_name)
            actor_info = ActorInfo(actor)
            for post in actor.post_list:
                if not post.completed:  # the post is not analysed yet
                    QueueUtil.enqueuePost(self.queueMgr, actor_info, post.post_id, None)
                else:  # all resources of the post are already added
                    QueueUtil.enqueueAllRes(self.queueMgr, actor_info, post, self.downloadLimit.file_size)

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

    def __repr__(self):
        return f"({self.desc}\tdownloadLimit={self.downloadLimit}"

    def toJson(self):
        worker_count_map = self.guarder.getWorkerCountMap()
        queue_count_map = self.queueMgr.getQueueCountMap()
        return {'uid': self.uid,
                'desc': self.desc,
                'download_limit': self.downloadLimit.toJson(),
                'worker_count': worker_count_map,
                'queue_count': queue_count_map,
                }
