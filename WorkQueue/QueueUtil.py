import os

import Consts
import LogUtil
from Models.BaseModel import ResState, PostModel
from WorkQueue import QueueMgr
from WorkQueue.ExtraInfo import ActorExtraInfo, PostExtraInfo, ResExtraInfo, ActorsExtraInfo, ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem


def enqueueActors(start_order: int = 0, from_url: str = None):
    out_extra = ActorsExtraInfo(start_order)
    url = Consts.formatActorsUrl(start_order)
    out_item = UrlQueueItem(url, from_url, out_extra)
    QueueMgr.add(QueueMgr.QueueType.Download, out_item)


def enqueueActor(actor_name: str, start_order: int = 0, from_url: str = None):
    out_extra = ActorExtraInfo(actor_name, start_order)
    url = Consts.formatUserUrl(actor_name, start_order)
    out_item = UrlQueueItem(url, from_url, out_extra)
    QueueMgr.add(QueueMgr.QueueType.Download, out_item)


def enqueuePost(actor_name: str, post_id: int, from_url: str):
    out_extra = PostExtraInfo(actor_name, post_id)
    url = Consts.formatPostUrl(actor_name, post_id)
    out_item = UrlQueueItem(url, from_url, out_extra)
    QueueMgr.add(QueueMgr.QueueType.Download, out_item)


def enqueueAllRes(post: PostModel):
    # post = PostCtrl.getPost(session, post_id)
    post_url = Consts.formatPostUrl(post.actor_name, post.post_id)
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
        if not res.shouldDownload():
            continue

        out_extra = ResExtraInfo(post.actor_name, post.post_id, res.res_id)
        out_item = UrlQueueItem(res.res_url, post_url, out_extra)
        if res.res_size == 0:
            QueueMgr.add(QueueMgr.QueueType.ResInfo, out_item)
        else:
            enqueueResFile(out_item, res.tmpFilePath(), res.res_size)



def enqueueResFile(item: UrlQueueItem, file_path: str, file_size: int):
    out_extra = ResFileExtraInfo(item.extra_info, file_path, file_size)
    out_item = UrlQueueItem(item.url, item.from_url, out_extra)
    QueueMgr.add(QueueMgr.QueueType.ResFile, out_item)


def enqueueResValid(item: UrlQueueItem):
    QueueMgr.add(QueueMgr.QueueType.ResValid, item)
