import asyncio
from datetime import datetime
import os

from sqlalchemy.orm import Session

import Configs
from Consts import DateFormat, PostFilter, ResType, TaskType, WorkerType
from Ctrls import ActorQueryCtrl, DbCtrl, ActorCtrl, PostCtrl, ActorGroupCtrl, ResCtrl, ResFileCtrl
from Download import WorkerMgr
from Download.DownloadLimit import DownloadLimit
from Download.TaskQueueMgr import TaskQueueMgr
from Models.ModelInfos import ActorInfo
from Utils import LogUtil, PyUtil
from routers.web_data import ActorUrl
from routers.schemas_others import DownloadTaskResponse, WorkerProcessStats


class DownloadTask:
    def __init__(self, task_uid, task_type: TaskType):
        self.uid = task_uid
        self.task_type = task_type

        self.running = False
        self.worker_tasks = []
        self.watcher_task: asyncio.Task | None = None
        self.queue_mgr = TaskQueueMgr(task_type)
        self.download_limit: DownloadLimit | None = None
        self.init_group_id = 0
        self.task_desc = ""
        self.task_arg = 0
        self.actor_ids = []
        self.worker_process_stats: dict[WorkerType, WorkerProcessStats] = {}

    @property
    def is_fix_posts(self) -> bool:
        return self.task_type == TaskType.FixPost

    @property
    def is_fix_res(self) -> bool:
        return self.task_type == TaskType.FixRes

    @property
    def wait_thumbnail(self) -> bool:
        return self.download_limit.allowResDownload(ResType.Image)

    def _getWorkerStats(self, worker_type: WorkerType) -> WorkerProcessStats:
        worker_stats = self.worker_process_stats.get(worker_type)
        if worker_stats is None:
            worker_stats = WorkerProcessStats(
                worker_type=worker_type.name,
                failed_count=0,
                process_count=0,
                total_process_time=0,
                last_process_time=""
            )
            self.worker_process_stats[worker_type] = worker_stats
        return worker_stats

    def onItemFailed(self, worker_type: WorkerType):
        worker_stats = self._getWorkerStats(worker_type)
        worker_stats.failed_count += 1

    def onItemProcessed(self, worker_type: WorkerType, process_time: float):
        worker_stats = self._getWorkerStats(worker_type)

        worker_stats.process_count += 1
        worker_stats.total_process_time += process_time
        worker_stats.last_process_time = PyUtil.format_now(DateFormat.Time)

    async def start(self):
        """
        new all threads and start running
        """
        if self.running:
            LogUtil.warning("Task is already running.")
            return
        self.running = True

        for worker_type in WorkerType:
            count = WorkerMgr.getWorkerCount(worker_type)
            for i in range(count):
                worker = WorkerMgr.createWorker(worker_type, self)
                # print(f"create worker {worker_type}")
                task = asyncio.create_task(worker.run())
                self.worker_tasks.append(task)

        self.watcher_task = asyncio.create_task(self._watch_completion())

    async def _watch_completion(self):
        """
        私有协程：在后台运行，等待所有队列完成工作。
        """
        try:
            # wait for all queues to finish
            await self.queue_mgr.wait_for_finish()
            LogUtil.info(f"Task {self.task_desc} queues finished.")
            # stop all workers by sending sentinel
            await self._notify_workers_to_stop()
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            LogUtil.info(f"Task {self.task_desc} workers stopped.")
            self.running = False
            LogUtil.info(f"Task {self.task_desc} finished.")

        except asyncio.CancelledError:
            LogUtil.info(f"Task {self.task_desc} was cancelled.")
        except Exception as e:
            LogUtil.error(f"Task {self.task_desc} crashed")
            LogUtil.exception(e)
        finally:
            self.watcher_task = None

    async def _notify_workers_to_stop(self):
        for worker_type in WorkerType:
            count = WorkerMgr.getWorkerCount(worker_type)
            queue_type = Configs.getQueueTypeByWorkerType(worker_type)
            for i in range(count):
                await self.queue_mgr.enqueueSentinel(queue_type)

    async def Stop(self):
        if not self.running:
            return
        self.running = False
        tasks_to_wait = list(self.worker_tasks)
        for task in self.worker_tasks:
            task.cancel()
        if self.watcher_task:
            self.watcher_task.cancel()
            tasks_to_wait.append(self.watcher_task)
        await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        LogUtil.info(f"Task {self.task_desc} stopped successfully.")

    def isDone(self) -> bool:
        return not self.running

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

    def is_all_posts(self) -> bool:
        return self.download_limit.getPostFilter() == PostFilter.All

    async def normalPosts(self, actor_ids: list[int]):
        for actor_id in actor_ids:
            await self.queue_mgr.enqueueFetchActor(actor_id)
            await self.queue_mgr.enqueueFetchActorLink(actor_id)

    async def completedPosts(self, actor_ids: list[int]):
        with DbCtrl.getSession() as session, session.begin():
            for actor_id in actor_ids:
                actor = ActorCtrl.getActor(session, actor_id)
                actor_info = ActorInfo(actor)
                posts = PostCtrl.getPostsOfActor(
                    session, actor_id, actor.last_post_id, True)
                for post in posts:
                    await self.queue_mgr.enqueueAllRes(
                        actor_info, post, self.download_limit)

    async def currentPosts(self, actor_ids: list[int]):
        with DbCtrl.getSession() as session, session.begin():
            for actor_id in actor_ids:
                actor = ActorCtrl.getActor(session, actor_id)
                actor_info = ActorInfo(actor)
                posts = PostCtrl.getPostsOfActor(
                    session, actor_id, actor.last_post_id)
                for post in posts:
                    if not post.completed:  # the post is not analysed yet
                        await self.queue_mgr.enqueueFetchPost(
                            actor_info, post)
                    else:  # all resources of the post are already added
                        await self.queue_mgr.enqueueAllRes(
                            actor_info, post, self.download_limit)

    async def downloadActors(self, actor_ids: list[int]):
        self.actor_ids = actor_ids
        post_filter = self.download_limit.getPostFilter()
        if post_filter == PostFilter.Normal or post_filter == PostFilter.All:
            await self.normalPosts(actor_ids)
        elif post_filter == PostFilter.Current:
            await self.currentPosts(actor_ids)
        elif post_filter == PostFilter.Completed:
            await self.completedPosts(actor_ids)
        else:
            raise Exception(f"Unknown post filter {post_filter}")

        await self.start()

    async def downloadByUrls(self, actor_urls: list[ActorUrl]):
        self.task_desc = "Specific Urls"
        actor_ids: list[int] = []
        with DbCtrl.getSession() as session, session.begin():
            for actor_url in actor_urls:
                href_list = actor_url.full_url.split("/")

                actor_info = ActorInfo()
                actor_info.actor_platform = href_list[-3]
                actor_info.actor_link = href_list[-1]
                actor_info.actor_name = actor_url.actor_name or href_list[-1]

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
        await self.downloadActors(actor_ids)

    async def downloadSpecificActor(self, actor_id: int):
        """
        download specific actors
        """
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            # in case linked actors found, set the group id to the actor's group id
            self.setInitGroup(actor.actor_group_id)
            self.task_desc = f"Specific Actor {actor.actor_name}"
            self.task_arg = actor_id
        await self.downloadActors([actor_id])

    async def downloadNewActors(self, start_page: int):
        """
        download new actors
        """
        self.task_desc = "New Actors"
        await self.queue_mgr.enqueueFetchActors(start_page)
        await self.start()

    async def downloadByActorGroup(self, group_id: int):
        """
        download actors in corresponding category
        """
        actor_ids = []
        with DbCtrl.getSession() as session, session.begin():
            group = ActorGroupCtrl.getActorGroup(session, group_id)
            self.task_desc = f"Actors in group {group.group_name}"
            self.task_arg = group_id
            actors = ActorQueryCtrl.getActorsByGroup(session, group_id)
            for actor in actors:
                actor_ids.append(actor.actor_id)
        await self.downloadActors(actor_ids)

    async def __resumeActor_Process(self, session: Session, file: str, post_id: int, res_index: int, extra_data: any = None):
        res = ResCtrl.getResByIndex(session, post_id, res_index)
        if res.shouldDownload(self.download_limit):
            await self.queue_mgr.enqueueResFile(res)

    async def resumeActor(self, actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None or not actor.actor_group.has_folder:
                return
            self.actor_ids = [actor_id]
            self.task_desc = f"resume actor {actor.actor_name}"
            self.task_arg = actor_id
            await ResFileCtrl.traverseDownloadingFilesOfActor_async(
                session, actor, self.__resumeActor_Process)

        await self.start()

    async def fix_more_posts(self, actor_id: int):
        if actor_id not in self.actor_ids:
            LogUtil.info(f"fix more actor {actor_id}")
            self.actor_ids.append(actor_id)
            await self.normalPosts([actor_id])

    async def fix_posts_of_actor(self, actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None:
                return
            ActorCtrl.refreshActorPostCount(session, actor_id)

            self.actor_ids = [actor_id]
            self.task_desc = f"fix posts of actor {actor.actor_name}"
            self.task_arg = actor_id
            await self.normalPosts(self.actor_ids)
        await self.start()

    async def _fix_video_urls_of_actor(self, session: Session, actor_info: ActorInfo, end_date: datetime):
        posts = PostCtrl.getPostsToFixVideoUrls(
            session, actor_info.actor_id, end_date)
        for post in posts:
            await self.queue_mgr.enqueueFetchPost(actor_info, post)

    async def fix_video_of_actor(self, actor_id: int, end_date: datetime):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None:
                return

            self.actor_ids = [actor_id]
            self.task_desc = f"fix video of actor {actor.actor_name}"
            self.task_arg = actor_id
            await self._fix_video_urls_of_actor(session, ActorInfo(actor), end_date)
        await self.start()

    async def fix_actor_link(self):
        pass

    async def fix_actor_icon(self):
        pass

    async def manual(self):
        """
        custom logic to fix bugs etc
        """
        self.task_desc = f"manual op"
        # TODO: implement manual logic
        actor_ids: list[int] = []
        with DbCtrl.getSession() as session, session.begin():
            actor_ids = ActorQueryCtrl.getActorsWithoutTotalPostCount(session)
        await self.downloadActors(actor_ids)

    @staticmethod
    def initEnv():
        """
        initialize the environment
        :return:
        """
        LogUtil.info("initializing environment...")
        # should be called before any other operations
        os.makedirs(Configs.getRootFolder(), exist_ok=True)
        os.makedirs(Configs.formatTmpFolderPath(), exist_ok=True)
        os.makedirs(Configs.formatIconFolderPath(), exist_ok=True)
        DbCtrl.init()

    def __repr__(self):
        return self.task_desc

    def toResponse(self, session: Session) -> DownloadTaskResponse:
        response = DownloadTaskResponse(
            uid=self.uid,
            type=self.task_type,
            arg=self.task_arg,
            download_limit=self.download_limit.toResponse(),
            worker_count=self.queue_mgr.get_worker_counts(),
            queue_count=self.queue_mgr.get_queue_counts(),
            worker_process_stats=sorted(
                list(self.worker_process_stats.values()), key=lambda x: x.worker_type)
        )
        if self.task_type < TaskType.MaxSingleActor:
            response.actor_abstract = ActorCtrl.getActorAbstract(
                session, self.task_arg)
        return response
