import os

import Configs
import Consts
from Ctrls import DbCtrl, ActorCtrl
from Download.DownloadLimit import DownloadLimit, PostFilter
from Guarder import Guarder
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.QueueMgr import QueueMgr
from Workers import WorkerMgr
from routers.web_data import ActorUrl


class DownloadTask(object):
    def __init__(self, task_uid):
        self.uid = task_uid
        self.guarder = Guarder(self)
        self.queueMgr = QueueMgr()
        self.downloadLimit: DownloadLimit = None
        self.init_category = 0
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

    def setInitCategory(self, category: int):
        """
        set initial category for new actors
        :return:
        """
        self.init_category = category

    def normalPosts(self, actor_names: list[str]):
        val = min(len(actor_names), Configs.MAX_FETCH_ACTOR_COUNT)
        self.worker_count[Consts.WorkerType.FetchActor] = val

        for actor_name in actor_names:
            QueueUtil.enqueueFetchActor(self.queueMgr, actor_name)

    def oldPosts(self, actor_names: list[str]):
        self.worker_count[Consts.WorkerType.FetchActor] = 0

        with DbCtrl.getSession() as session, session.begin():
            for actor_name in actor_names:
                actor = ActorCtrl.getActor(session, actor_name)
                actor_info = ActorInfo(actor)
                for post in actor.post_list:
                    if not post.completed:  # the post is not analysed yet
                        QueueUtil.enqueuePost(self.queueMgr, actor_info, post.post_id, None)
                    else:  # all resources of the post are already added
                        QueueUtil.enqueueAllRes(self.queueMgr, actor_info, post, self.downloadLimit)

    def downloadActors(self, actor_names: list[str]):
        self.worker_count[Consts.WorkerType.FetchActors] = 0
        if self.downloadLimit.post_filter == PostFilter.Old:
            self.oldPosts(actor_names)
        else:
            self.normalPosts(actor_names)

        self.startDownload()

    def downloadByUrls(self, actor_urls: list[ActorUrl]):
        self.desc = "Specific Urls"
        actor_names = []
        with DbCtrl.getSession() as session, session.begin():
            for actor_url in actor_urls:
                href_list = actor_url.full_url.split("/")

                actor_info = ActorInfo()
                actor_info.actor_platform = href_list[-3]
                actor_info.actor_link = href_list[-1]
                actor_info.actor_name = actor_url.actor_name

                QueueUtil.enqueueActorIcon(self.queueMgr, actor_info)
                # enqueue actor if not exists
                if not ActorCtrl.hasActor(session, actor_info.actor_name):
                    ActorCtrl.addActor(session, actor_info, self.init_category)
                actor_names.append(actor_info.actor_name)
            session.flush()
        self.downloadActors(actor_names)

    def downloadSpecificActor(self, actor_name: str):
        """
        download specific actors
        """
        self.desc = f"Specific Actor {actor_name}"
        self.downloadActors([actor_name])

    def downloadNewActors(self):
        """
        download new actors
        """
        self.desc = "New Actors."
        QueueUtil.enqueueFetchActors(self.queueMgr)
        self.startDownload()

    def downloadByActorCategory(self, actor_category: int):
        """
        download actors in corresponding category
        """
        self.desc = f"Actors in group {actor_category}."
        actor_names = []
        with DbCtrl.getSession() as session, session.begin():
            actors = ActorCtrl.getActorsByCategory(session, actor_category)
            for actor in actors:
                actor_names.append(actor.actor_name)
        self.downloadActors(actor_names)

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
