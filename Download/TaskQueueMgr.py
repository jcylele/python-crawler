from Consts import QueueType, TaskType
from Ctrls import RequestCtrl
from Download.DownloadLimit import DownloadLimit
from Download.QueueMgr import QueueMgr
from Models.ModelInfos import ActorInfo, PostInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from WorkQueue.ExtraInfo import ResFileExtraInfo, ResInfoExtraInfo
from WorkQueue.FetchQueueItem import (FetchActorQueueItem,
                                      FetchActorsQueueItem, FetchPostQueueItem)
from WorkQueue.UrlQueueItem import UrlQueueItem


class TaskQueueMgr(QueueMgr):
    def __init__(self, task_type: TaskType):
        super().__init__()
        self.can_fetch_actor = self.canFetchActor(task_type)
        self.can_fetch_post = self.canFetchPost(task_type)
        self.can_fetch_res = self.canFetchRes(task_type)

    def canFetchActor(self, task_type: TaskType) -> bool:
        return True

    def canFetchPost(self, task_type: TaskType) -> bool:
        return task_type not in [TaskType.New, TaskType.FixPost, TaskType.Manual, TaskType.Thumbnail]

    def canFetchRes(self, task_type: TaskType) -> bool:
        return task_type not in [TaskType.New, TaskType.FixPost, TaskType.Manual, TaskType.Thumbnail]

    async def enqueueFetchActors(self, start_page: int):
        item = FetchActorsQueueItem(start_page)
        await self.put(QueueType.FetchActors, item)

    async def enqueueFetchActor(self, actor_id: int):
        if not self.can_fetch_actor:
            return
        item = FetchActorQueueItem(actor_id)
        await self.put(QueueType.FetchActor, item)

    async def enqueueFetchActorLink(self, actor_id: int):
        if not self.can_fetch_actor:
            return
        item = FetchActorQueueItem(actor_id)
        await self.put(QueueType.FetchActorLink, item)

    async def enqueueFetchPost(self, actor_info: ActorInfo, post_info: PostInfo | PostModel):
        if not self.can_fetch_post:
            return
        item = FetchPostQueueItem(actor_info, post_info)
        await self.put(QueueType.FetchPost, item)

    async def enqueueAllRes(self, actor_info: ActorInfo, post: PostModel, downloadLimit: DownloadLimit):
        if not self.can_fetch_res:
            return
        post_url = RequestCtrl.formatPostUrl(
            actor_info, post.post_id_str)
        for res in post.res_list: # type: ResModel
            if res.isCompleted():
                continue

            out_extra = ResInfoExtraInfo(
                actor_info, post.post_id, res.res_id, res.res_type)
            out_item = UrlQueueItem(
                res.full_url(), post_url, out_extra)
            if res.res_size == 0:
                if downloadLimit.allowResInfo(res.res_type):
                    await self.put(QueueType.ResInfo, out_item)
            elif res.shouldDownload(downloadLimit):
                await self.downloadResFile(out_item, res.tmpFilePath(), res.res_size)

    async def enqueueResFile(self, res: ResModel):
        if not self.can_fetch_res:
            return
        post = res.post
        actor_info = ActorInfo(post.actor)
        post_url = RequestCtrl.formatPostUrl(
            actor_info, post.post_id_str)
        out_extra = ResInfoExtraInfo(
            actor_info, post.post_id, res.res_id, res.res_type)
        out_item = UrlQueueItem(res.full_url(), post_url, out_extra)
        await self.downloadResFile(out_item, res.tmpFilePath(), res.res_size)

    async def downloadResFile(self, item: UrlQueueItem, file_path: str, file_size: int):
        if not self.can_fetch_res:
            return
        out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
        out_item = UrlQueueItem(item.url, item.from_url, out_extra)
        await self.put(QueueType.FileDownload, out_item)

    async def requeueItem(self, queueType: QueueType, item: UrlQueueItem) -> bool:
        item.onFailed()
        if item.shouldRetry():
            await self.put(queueType, item)
            return True
        return False

    async def enqueueResValid(self, item: UrlQueueItem):
        if not self.can_fetch_res:
            return
        await self.put(QueueType.ResValid, item)
