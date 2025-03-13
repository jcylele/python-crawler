# shared functions for queue related operations

import os

import Configs
from Consts import QueueType
from Ctrls import RequestCtrl
from Download.DownloadLimit import DownloadLimit
from Models.ActorInfo import ActorInfo
from Models.BaseModel import ResState, PostModel, ResModel
from Utils import LogUtil
from Download import QueueMgr
from WorkQueue.ExtraInfo import ResInfoExtraInfo, ResFileExtraInfo, \
    ActorIconExtraInfo
from WorkQueue.FetchQueueItem import FetchActorsQueueItem, FetchActorQueueItem, FetchPostQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem


def enqueueFetchActors(queueMgr: QueueMgr, from_start: bool):
    item = FetchActorsQueueItem(from_start)
    queueMgr.put(QueueType.FetchActors, item)


def enqueueFetchActor(queueMgr: QueueMgr, actor_id: int):
    item = FetchActorQueueItem(actor_id)
    queueMgr.put(QueueType.FetchActor, item)


def enqueueFetchActorLink(queueMgr: QueueMgr, actor_id: int):
    item = FetchActorQueueItem(actor_id)
    queueMgr.put(QueueType.FetchActorLink, item)


def enqueueFetchPost(queueMgr: QueueMgr, actor_info: ActorInfo, post_id: int, is_dm: bool):
    item = FetchPostQueueItem(actor_info, post_id, is_dm)
    queueMgr.put(QueueType.FetchPost, item)


def enqueueAllRes(queueMgr: QueueMgr, actor_info: ActorInfo, post: PostModel, downloadLimit: DownloadLimit):
    # post = PostCtrl.getPost(session, post_id)
    post_url = RequestCtrl.formatPostUrl(actor_info, post.post_id, post.is_dm)
    for res in post.res_list:
        # 文件已下载,检查大小
        file_path = res.filePath()
        if os.path.exists(file_path):
            real_size = os.path.getsize(file_path)
            if real_size < res.res_size:
                LogUtil.warn(
                    f"{file_path} deleted because of incorrect size, expect {res.res_size:,d} get {real_size:,d}")
                os.remove(file_path)
                res.setState(ResState.Init)
            else:
                res.setState(ResState.Down)
                continue

        out_extra = ResInfoExtraInfo(actor_info, post.post_id, res.res_id, res.res_type)
        out_item = UrlQueueItem(res.res_url, post_url, out_extra)
        # 所有资源都Info
        if res.res_size == 0:
            queueMgr.put(QueueType.ResInfo, out_item)
            continue
        elif res.shouldDownload(downloadLimit):
            downloadResFile(queueMgr, out_item, res.tmpFilePath(), res.res_size)


def enqueueResFile(queueMgr: QueueMgr, actor_info: ActorInfo, post: PostModel, res: ResModel):
    post_url = RequestCtrl.formatPostUrl(actor_info, post.post_id, post.is_dm)
    out_extra = ResInfoExtraInfo(actor_info, post.post_id, res.res_id, res.res_type)
    out_item = UrlQueueItem(res.res_url, post_url, out_extra)
    downloadResFile(queueMgr, out_item, res.tmpFilePath(), res.res_size)


def downloadResFile(queueMgr: QueueMgr, item: UrlQueueItem, file_path: str, file_size: int):
    out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
    out_item = UrlQueueItem(item.url, item.from_url, out_extra)
    queueMgr.put(QueueType.FileDownload, out_item)


def putbackResFile(queueMgr: QueueMgr, item: UrlQueueItem):
    item.onFailed()
    if item.shouldRetry():
        queueMgr.put(QueueType.FileDownload, item)


def enqueueResValid(queueMgr: QueueMgr, item: UrlQueueItem):
    queueMgr.put(QueueType.ResValid, item)


def enqueueActorIcon(queueMgr: QueueMgr, actor_info: ActorInfo, from_url: str):
    # same actor_name on different platform, so use {actor_name}_{platform}.png
    file_path = actor_info.icon_file_path()
    # skip is exist
    if os.path.exists(file_path):
        return
    out_extra = ActorIconExtraInfo(actor_info)
    url = RequestCtrl.formatActorIconUrl(actor_info)
    out_item = UrlQueueItem(url, from_url, out_extra)
    queueMgr.put(QueueType.SimpleFile, out_item)
