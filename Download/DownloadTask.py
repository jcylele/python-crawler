import os
import re

import Configs
import Consts
from Ctrls import DbCtrl, ActorCtrl, PostCtrl, ActorGroupCtrl, ResCtrl
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
        self.init_group_id = 0
        self.desc = ""
        self.worker_count = {}
        self.actor_ids = []

    def setWorkerCount(self, work_type: Consts.WorkerType, count: int):
        self.worker_count[work_type] = count

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
        self.queueMgr.clear()

    def isDone(self) -> bool:
        return self.guarder.done

    def setLimit(self, limit: DownloadLimit):
        """
        set download limit
        """
        self.downloadLimit = limit

    def setInitGroup(self, group_id: int):
        """
        set initial category for new actors
        :return:
        """
        self.init_group_id = group_id

    def normalPosts(self, actor_ids: list[int]):
        val = min(len(actor_ids), Configs.MAX_FETCH_ACTOR_COUNT)
        self.setWorkerCount(Consts.WorkerType.FetchActor, val)

        for actor_id in actor_ids:
            QueueUtil.enqueueFetchActor(self.queueMgr, actor_id)

    def currentPosts(self, actor_ids: list[int]):
        self.setWorkerCount(Consts.WorkerType.FetchActor, 0)

        with DbCtrl.getSession() as session, session.begin():
            for actor_id in actor_ids:
                actor = ActorCtrl.getActor(session, actor_id)
                actor_info = ActorInfo(actor)
                posts = PostCtrl.getNewPosts(session, actor_id, actor.last_post_id)
                has_unfinished_posts = False
                for post in posts:
                    if not post.completed:  # the post is not analysed yet
                        has_unfinished_posts = True
                        # QueueUtil.enqueuePost(self.queueMgr, actor_info, post.post_id, post.is_dm, None)
                        QueueUtil.enqueueFetchPost(self.queueMgr, actor_info, post.post_id, post.is_dm)
                    else:  # all resources of the post are already added
                        QueueUtil.enqueueAllRes(self.queueMgr, actor_info, post, self.downloadLimit)
                if not has_unfinished_posts:
                    self.setWorkerCount(Consts.WorkerType.FetchPost, 0)

    def downloadActors(self, actor_ids: list[int]):
        self.actor_ids = actor_ids
        self.setWorkerCount(Consts.WorkerType.FetchActors, 0)
        if self.downloadLimit.post_filter == PostFilter.Current:
            self.currentPosts(actor_ids)
        else:
            self.normalPosts(actor_ids)

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

                QueueUtil.enqueueActorIcon(self.queueMgr, actor_info)
                # enqueue actor if not exists
                if not ActorCtrl.hasActor(session, actor_info):
                    actor = ActorCtrl.addActor(session, actor_info, self.init_group_id)
                    actor_ids.append(actor.actor_id)
            session.flush()
        self.downloadActors(actor_ids)

    def downloadSpecificActor(self, actor_id: int):
        """
        download specific actors
        """
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            self.desc = f"Specific Actor {actor.actor_name}"
        self.downloadActors([actor_id])

    def downloadNewActors(self):
        """
        download new actors
        """
        self.desc = "New Actors."
        QueueUtil.enqueueFetchActors(self.queueMgr)
        self.startDownload()

    def downloadByActorGroup(self, group_id: int):
        """
        download actors in corresponding category
        """
        actor_ids = []
        with DbCtrl.getSession() as session, session.begin():
            group = ActorGroupCtrl.getActorGroup(session, group_id)
            self.desc = f"Actors in group {group.group_name}."

            actors = ActorCtrl.getActorsByGroup(session, group_id)
            for actor in actors:
                actor_ids.append(actor.actor_id)
        self.downloadActors(actor_ids)

    def resumeFiles(self):
        self.desc = f"resume files"
        # cache folder status
        folder_dict = {}
        download_folder = Configs.formatTmpFolderPath()
        with DbCtrl.getSession() as session, session.begin():
            try:
                for root, _, files in os.walk(download_folder):
                    for file in files:
                        matchObj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file)
                        if matchObj is None:
                            continue
                        actor_name = matchObj.group(1)
                        # get and cache folder status
                        actor_info = folder_dict.get(actor_name)
                        if actor_info is None:
                            actor = ActorCtrl.getActorByName(session, actor_name)
                            if actor is not None and actor.actor_group.has_folder:
                                actor_info = ActorInfo(actor)
                                folder_dict[actor_name] = actor_info
                            else:
                                folder_dict[actor_name] = False

                        # remove file if actor not exist or has no folder
                        if actor_info is None:
                            LogUtil.info(f"remove file {file} due to actor")
                            os.remove(os.path.join(root, file))
                        else:
                            post_id = int(matchObj.group(2))
                            res_index = int(matchObj.group(3))
                            res = ResCtrl.getResByIndex(session, post_id, res_index)
                            if res is None or res.res_state == Consts.ResState.Del:
                                LogUtil.info(f"remove file {file} due to res")
                                os.remove(os.path.join(root, file))
                            elif res.shouldDownload(self.downloadLimit):
                                QueueUtil.enqueueResFile(self.queueMgr, actor_info, res.post, res)
            except Exception as e:
                pass
        # no need to fetch actors
        self.setWorkerCount(Consts.WorkerType.FetchActors, 0)
        self.setWorkerCount(Consts.WorkerType.FetchActor, 0)
        self.startDownload()

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
