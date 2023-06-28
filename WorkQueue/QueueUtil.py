# shared functions for queue related operations

import os

import Configs
from Consts import QueueType
from Ctrls import RequestCtrl
from Models.ActorInfo import ActorInfo
from Models.BaseModel import ResState, PostModel
from Utils import LogUtil
from WorkQueue import QueueMgr
from WorkQueue.ExtraInfo import PostExtraInfo, ResInfoExtraInfo, ResFileExtraInfo, \
    FilePathExtraInfo
from WorkQueue.FetchQueueItem import FetchActorsQueueItem, FetchActorQueueItem
from WorkQueue.UrlQueueItem import UrlQueueItem


def enqueueFetchActors(queueMgr: QueueMgr):
    item = FetchActorsQueueItem()
    queueMgr.put(QueueType.FetchActors, item)


def enqueueFetchActor(queueMgr: QueueMgr, actor_name: str):
    item = FetchActorQueueItem(actor_name)
    queueMgr.put(QueueType.FetchActor, item)


def enqueuePost(queueMgr: QueueMgr, actor_info: ActorInfo, post_id: int, from_url: str):
    out_extra = PostExtraInfo(actor_info, post_id)
    url = RequestCtrl.formatPostUrl(actor_info, post_id)
    out_item = UrlQueueItem(url, from_url, out_extra)
    queueMgr.put(QueueType.PageDownload, out_item)


def enqueueAllRes(queueMgr: QueueMgr, actor_info: ActorInfo, post: PostModel, max_file_size: int):
    # post = PostCtrl.getPost(session, post_id)
    post_url = RequestCtrl.formatPostUrl(actor_info, post.post_id)
    for res in post.res_list:
        # 文件已下载,检查大小
        file_path = res.filePath()
        if os.path.exists(file_path):
            real_size = os.path.getsize(file_path)
            if real_size < res.res_size:
                LogUtil.warn(
                    f"{file_path} deleted because of incorrect size, expect {res.res_size:,d} get {real_size:,d}")
                os.remove(file_path)
                res.res_state = ResState.Init
            else:
                res.res_state = ResState.Down
                continue

        # 不需要下载
        if not res.shouldDownload(max_file_size):
            continue

        out_extra = ResInfoExtraInfo(actor_info, post.post_id, res.res_id)
        out_item = UrlQueueItem(res.res_url, post_url, out_extra)
        if res.res_size == 0:
            queueMgr.put(QueueType.ResInfo, out_item)
        else:
            enqueueResFile(queueMgr, out_item, res.tmpFilePath(), res.res_size)


def enqueueResFile(queueMgr: QueueMgr, item: UrlQueueItem, file_path: str, file_size: int):
    out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
    out_item = UrlQueueItem(item.url, item.from_url, out_extra)
    queueMgr.put(QueueType.FileDownload, out_item)


def putbackResFile(queueMgr: QueueMgr, item: UrlQueueItem):
    item.onFailed()
    if item.shouldRetry():
        queueMgr.put(QueueType.FileDownload, item)


def enqueueResValid(queueMgr: QueueMgr, item: UrlQueueItem):
    queueMgr.put(QueueType.ResValid, item)


def enqueueActorIcon(queueMgr: QueueMgr, actor_info: ActorInfo):
    file_path = f"{Configs.formatIconFolderPath()}/{actor_info.actor_name}.jfif"
    out_extra = FilePathExtraInfo(file_path)
    url = RequestCtrl.formatActorIconUrl(actor_info.actor_platform, actor_info.actor_link)
    out_item = UrlQueueItem(url, None, out_extra)
    queueMgr.put(QueueType.SimpleFile, out_item)
