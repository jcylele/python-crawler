
import os

from Consts import QueueType
from Ctrls import RequestCtrl
from Download.DownloadLimit import DownloadLimit
from Download.QueueMgr import QueueMgr
from Models.ActorInfo import ActorInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from WorkQueue.ExtraInfo import ResInfoExtraInfo, ResFileExtraInfo, ActorIconExtraInfo
from WorkQueue.FetchQueueItem import FetchActorsQueueItem, FetchActorQueueItem, FetchPostQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem


class TaskQueueMgr(QueueMgr):
    def __init__(self):
        super().__init__()

    def enqueueFetchActors(self, start_page: int):
        item = FetchActorsQueueItem(start_page)
        self.put(QueueType.FetchActors, item)

    def enqueueFetchActor(self, actor_id: int):
        item = FetchActorQueueItem(actor_id)
        self.put(QueueType.FetchActor, item)

    def enqueueFetchActorLink(self, actor_id: int):
        item = FetchActorQueueItem(actor_id)
        self.put(QueueType.FetchActorLink, item)

    def enqueueFetchPost(self, actor_info: ActorInfo, post_id: int, is_dm: bool):
        item = FetchPostQueueItem(actor_info, post_id, is_dm)
        self.put(QueueType.FetchPost, item)

    def enqueueAllRes(self, actor_info: ActorInfo, post: PostModel, downloadLimit: DownloadLimit):
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
                    self.put(QueueType.ResInfo, out_item)
            elif res.shouldDownload(downloadLimit):
                self.downloadResFile(out_item, res.tmpFilePath(), res.res_size)

    def enqueueResFile(self, res: ResModel):
        post = res.post
        actor_info = ActorInfo(post.actor)
        post_url = RequestCtrl.formatPostUrl(
            actor_info, post.post_id, post.is_dm)
        out_extra = ResInfoExtraInfo(
            actor_info, post.post_id, res.res_id, res.res_type)
        out_item = UrlQueueItem(res.full_url(), post_url, out_extra)
        self.downloadResFile(out_item, res.tmpFilePath(), res.res_size)

    def downloadResFile(self, item: UrlQueueItem, file_path: str, file_size: int):
        out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
        out_item = UrlQueueItem(item.url, item.from_url, out_extra)
        self.put(QueueType.FileDownload, out_item)

    def putbackResFile(self, item: UrlQueueItem):
        item.onFailed()
        if item.shouldRetry():
            self.put(QueueType.FileDownload, item)

    def enqueueResValid(self, item: UrlQueueItem):
        self.put(QueueType.ResValid, item)

    def enqueueActorIcon(self, actor_info: ActorInfo, from_url: str):
        # same actor_name on different platform, so use {actor_name}_{platform}.png
        file_path = actor_info.icon_file_path()
        # skip is exist
        if os.path.exists(file_path):
            return
        out_extra = ActorIconExtraInfo(actor_info)
        url = RequestCtrl.formatActorIconUrl(actor_info)
        out_item = UrlQueueItem(url, from_url, out_extra)
        self.put(QueueType.SimpleFile, out_item)
