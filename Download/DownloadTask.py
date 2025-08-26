import os


from sqlalchemy.orm import Session

import Configs
from Consts import PostFilter, WorkerType
from Ctrls import ActorQueryCtrl, DbCtrl, ActorCtrl, PostCtrl, ActorGroupCtrl, ResCtrl, ResFileCtrl
from Download import WorkerMgr
from Download.DownloadLimit import DownloadLimit
from Download.TaskQueueMgr import TaskQueueMgr
from Guarder import Guarder
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from routers.web_data import ActorUrl
from routers.schemas_others import DownloadTaskResponse

class DownloadTask(object):
    def __init__(self, task_uid):
        self.uid = task_uid
        self.guarder = Guarder(self)
        self.queueMgr = TaskQueueMgr()
        self.download_limit: DownloadLimit = None
        self.init_group_id = 0
        self.desc = ""
        self.actor_ids = []
        self.is_fix_posts = False

    def is_all_posts(self):
        return self.download_limit.getPostFilter() == PostFilter.All

    def startDownload(self):
        """
        new all threads and start running
        """
        for worker_type in WorkerType:
            count = WorkerMgr.getWorkerCount(worker_type)
            for i in range(count):
                worker = WorkerMgr.createWorker(worker_type, self)
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
        self.download_limit = limit

    def setInitGroup(self, group_id: int):
        """
        set initial category for new actors
        :return:
        """
        self.init_group_id = group_id

    def normalPosts(self, actor_ids: list[int]):
        for actor_id in actor_ids:
            self.queueMgr.enqueueFetchActor(actor_id)
            self.queueMgr.enqueueFetchActorLink(actor_id)

    def completedPosts(self, actor_ids: list[int]):
        with DbCtrl.getSession() as session, session.begin():
            for actor_id in actor_ids:
                actor = ActorCtrl.getActor(session, actor_id)
                actor_info = ActorInfo(actor)
                posts = PostCtrl.getCompletedPosts(
                    session, actor_id, actor.last_post_id)
                for post in posts:
                    self.queueMgr.enqueueAllRes(
                        actor_info, post, self.download_limit)

    def currentPosts(self, actor_ids: list[int]):
        with DbCtrl.getSession() as session, session.begin():
            for actor_id in actor_ids:
                actor = ActorCtrl.getActor(session, actor_id)
                actor_info = ActorInfo(actor)
                posts = PostCtrl.getNewPosts(
                    session, actor_id, actor.last_post_id)
                for post in posts:
                    if not post.completed:  # the post is not analysed yet
                        self.queueMgr.enqueueFetchPost(
                            actor_info, post.post_id, post.is_dm)
                    else:  # all resources of the post are already added
                        self.queueMgr.enqueueAllRes(
                            actor_info, post, self.download_limit)

    def downloadActors(self, actor_ids: list[int]):
        self.actor_ids = actor_ids
        post_filter = self.download_limit.getPostFilter()
        if post_filter == PostFilter.Normal or post_filter == PostFilter.All:
            self.normalPosts(actor_ids)
        elif post_filter == PostFilter.Current:
            self.currentPosts(actor_ids)
        elif post_filter == PostFilter.Completed:
            self.completedPosts(actor_ids)
        else:
            raise Exception(f"Unknown post filter {post_filter}")

        self.startDownload()

    def downloadByUrls(self, actor_urls: list[ActorUrl]):
        self.desc = "Specific Urls"
        actor_ids: list[int] = []
        with DbCtrl.getSession() as session, session.begin():
            for actor_url in actor_urls:
                href_list = actor_url.full_url.split("/")

                actor_info = ActorInfo()
                actor_info.actor_platform = href_list[-3]
                actor_info.actor_link = href_list[-1]
                actor_info.actor_name = actor_url.actor_name

                # enqueue actor if not exists
                actor = ActorCtrl.getActorByInfo(session, actor_info)
                if actor is None:
                    actor = ActorCtrl.addActor(
                        session, actor_info, self.init_group_id)
                    actor_ids.append(actor.actor_id)
                else:
                    LogUtil.info(
                        f"actor {actor_info.actor_name} already exists")
        # print(actor_ids)
        self.downloadActors(actor_ids)

    def downloadSpecificActor(self, actor_id: int):
        """
        download specific actors
        """
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            # in case linked actors found, set the group id to the actor's group id
            self.setInitGroup(actor.actor_group_id)
            self.desc = f"Specific Actor {actor.actor_name}"
        self.downloadActors([actor_id])

    def downloadNewActors(self, start_page: int):
        """
        download new actors
        """
        self.desc = "New Actors."
        self.queueMgr.enqueueFetchActors(start_page)
        self.startDownload()

    def downloadByActorGroup(self, group_id: int):
        """
        download actors in corresponding category
        """
        actor_ids = []
        with DbCtrl.getSession() as session, session.begin():
            group = ActorGroupCtrl.getActorGroup(session, group_id)
            self.desc = f"Actors in group {group.group_name}."

            actors = ActorQueryCtrl.getActorsByGroup(session, group_id)
            for actor in actors:
                actor_ids.append(actor.actor_id)
        self.downloadActors(actor_ids)

    def __resumeActor_Process(self, session: Session, file: str, post_id: int, res_index: int):
        res = ResCtrl.getResByIndex(session, post_id, res_index)
        if res.shouldDownload(self.download_limit):
            self.queueMgr.enqueueResFile(res)

    def resumeActor(self, actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None or not actor.actor_group.has_folder:
                return
            self.desc = f"resume actor {actor.actor_name}"
            self.actor_ids = [actor_id]

            ResFileCtrl.traverseDownloadingFilesOfActor(
                session, actor, self.__resumeActor_Process)

        self.startDownload()

    def fix_more_posts(self, actor_id: int):
        if actor_id not in self.actor_ids:
            LogUtil.info(f"fix more actor {actor_id}")
            self.actor_ids.append(actor_id)
            self.normalPosts([actor_id])

    def fix_posts_of_actor(self, actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None:
                return
            ActorCtrl.refreshActorPostCount(session, actor_id)

            self.is_fix_posts = True
            self.desc = f"fix posts of actor {actor.actor_name}"
            self.actor_ids = [actor_id]
            self.normalPosts(self.actor_ids)
            self.startDownload()

    def manual(self):
        """
        custom logic to fix bugs etc
        """
        self.desc = f"manual op"
        # TODO: implement manual logic

    @staticmethod
    def initEnv():
        """
        initialize the environment
        :return:
        """
        LogUtil.info("initializing environment...")
        # should be called before any other operations
        Configs.init()
        os.makedirs(Configs.RootFolder, exist_ok=True)
        os.makedirs(Configs.formatTmpFolderPath(), exist_ok=True)
        os.makedirs(Configs.formatIconFolderPath(), exist_ok=True)
        DbCtrl.init()

    def __repr__(self):
        return self.desc

    def toResponse(self) -> DownloadTaskResponse:
        return DownloadTaskResponse(
            uid=self.uid,
            desc=self.desc,
            download_limit=self.download_limit.toResponse(),
            worker_count=self.guarder.getWorkerCountMap(),
            queue_count=self.queueMgr.getQueueCountMap()
        )
