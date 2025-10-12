from Consts import QueueType
from Ctrls import RequestCtrl
from Download.DownloadLimit import DownloadLimit
from Download.QueueMgr import QueueMgr
from Models.ActorInfo import ActorInfo
from Models.PostInfo import PostInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from WorkQueue.ExtraInfo import ResInfoExtraInfo, ResFileExtraInfo
from WorkQueue.FetchQueueItem import FetchActorsQueueItem, FetchActorQueueItem, FetchPostQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem


class TaskQueueMgr(QueueMgr):
    def __init__(self):
        super().__init__()

    async def enqueueFetchActors(self, start_page: int):
        item = FetchActorsQueueItem(start_page)
        await self.put(QueueType.FetchActors, item)

    async def enqueueFetchActor(self, actor_id: int):
        item = FetchActorQueueItem(actor_id)
        await self.put(QueueType.FetchActor, item)

    async def enqueueFetchActorLink(self, actor_id: int):
        item = FetchActorQueueItem(actor_id)
        await self.put(QueueType.FetchActorLink, item)

    async def enqueueFetchPost(self, actor_info: ActorInfo, post_info: PostInfo|PostModel):
        item = FetchPostQueueItem(actor_info, post_info)
        await self.put(QueueType.FetchPost, item)

    async def enqueueAllRes(self, actor_info: ActorInfo, post: PostModel, downloadLimit: DownloadLimit):
        # post = PostCtrl.getPost(session, post_id)
        post_url = RequestCtrl.formatPostUrl(
            actor_info, post.post_id, post.is_dm)
        for res in post.res_list:
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
        post = res.post
        actor_info = ActorInfo(post.actor)
        post_url = RequestCtrl.formatPostUrl(
            actor_info, post.post_id, post.is_dm)
        out_extra = ResInfoExtraInfo(
            actor_info, post.post_id, res.res_id, res.res_type)
        out_item = UrlQueueItem(res.full_url(), post_url, out_extra)
        await self.downloadResFile(out_item, res.tmpFilePath(), res.res_size)

    async def downloadResFile(self, item: UrlQueueItem, file_path: str, file_size: int):
        out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
        out_item = UrlQueueItem(item.url, item.from_url, out_extra)
        await self.put(QueueType.FileDownload, out_item)

    async def requeueItem(self, queueType: QueueType, item: UrlQueueItem):
        item.onFailed()
        if item.shouldRetry():
            await self.put(queueType, item)

    async def enqueueResValid(self, item: UrlQueueItem):
        await self.put(QueueType.ResValid, item)
