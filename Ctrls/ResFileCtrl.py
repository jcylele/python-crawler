"""
ResFileCtrl is responsible for traversing related files of the resources.
"""

import asyncio
import os
import re
from typing import Any, Coroutine
from collections.abc import Callable
from sqlalchemy.orm import Session

import Configs
from Consts import ActorLogType, ResState, ResType
from Ctrls import ActorLogCtrl, ResCtrl
from Models.ActorModel import ActorModel
from Models.PostModel import PostModel
from Utils import DirUtil, LogUtil
from routers.schemas_others import ActorAbstract, ResFileInfo, DownloadingVideoStats

# region traverse file functions


def traverseActorFolders(session: Session, callback: Callable[[Session, str, str, int, any], None], extra_data: any = None):
    with os.scandir(Configs.getRootFolder()) as it:
        try:
            for entry in it:
                if entry.is_file():
                    continue
                match_obj = re.match(r'^(\S+)_(\d+)$', entry.name)
                if match_obj is None:
                    continue
                actor_name = match_obj.group(1)
                actor_id = int(match_obj.group(2))
                callback(session, entry.path, actor_name, actor_id, extra_data)
        except Exception as e:
            LogUtil.error(f"traverseActorFolders failed, get Error")
            LogUtil.exception(e)
            pass


def traverseDownloadedFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int, any], None], extra_data: any = None):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)

    with os.scandir(actor_folder) as it:
        for entry in it:
            if entry.is_dir():
                continue
            match_obj = re.match(r'^(?:[lp]_)?(\d+)_(\d+)\.\w+$', entry.name)
            if match_obj is None:
                continue
            post_id = int(match_obj.group(1))
            res_index = int(match_obj.group(2))
            callback(session, entry.path, post_id, res_index, extra_data)


def traverseDownloadingFiles(session: Session, callback: Callable[[Session, str, int, int, any], None], extra_data: any = None):
    download_folder = Configs.formatTmpFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))
                callback(session, entry.path, post_id, res_index, extra_data)
    except Exception as e:
        LogUtil.error(f"traverseDownloadingFiles failed, get Error")
        LogUtil.exception(e)
        pass


def existDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int, any], bool], extra_data: any = None) -> bool:
    download_folder = Configs.formatTmpFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                actor_name = match_obj.group(1)
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))
                if actor_name != actor.actor_name:
                    continue
                post = session.get(PostModel, post_id)
                if post is None:
                    continue
                if post.actor_id != actor.actor_id:
                    continue
                if callback(session, entry.path, post_id, res_index, extra_data):
                    return True
    except Exception as e:
        LogUtil.error(
            f"existDownloadingFilesOfActor {actor.actor_name} failed, get error")
        LogUtil.exception(e)

    return False


def traverseDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int, any], None], extra_data: any = None):
    download_folder = Configs.formatTmpFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                actor_name = match_obj.group(1)
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))
                if actor_name != actor.actor_name:
                    continue
                post = session.get(PostModel, post_id)
                if post is None:
                    continue
                if post.actor_id != actor.actor_id:
                    continue
                callback(session, entry.path, post_id, res_index, extra_data)
    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor {actor.actor_name} failed, get error")
        LogUtil.exception(e)


async def traverseDownloadingFilesOfActor_async(session: Session, actor: ActorModel,
                                                callback: Callable[[Session, str, int, int], Coroutine[Any, Any, None]],
                                                extra_data: any = None):
    """
    traverseDownloadingFilesOfActor 的异步版本
    """

    try:
        download_folder = Configs.formatTmpFolderPath()
        all_file_names = os.listdir(download_folder)

        callback_tasks = []
        for file_name in all_file_names:
            match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file_name)
            if not match_obj:
                continue

            actor_name = match_obj.group(1)
            if actor_name != actor.actor_name:
                continue

            post_id = int(match_obj.group(2))
            res_index = int(match_obj.group(3))

            # 注意: session.get() 是一个同步的数据库调用。
            # 如果这里成为性能瓶颈，可以考虑使用异步数据库驱动和异步 session。
            post = session.get(PostModel, post_id)
            if post is None or post.actor_id != actor.actor_id:
                continue

            # 创建一个异步回调任务
            callback_tasks.append(
                callback(session, os.path.join(
                    download_folder, file_name), post_id, res_index, extra_data)
            )

        # 并发执行所有回调任务
        if callback_tasks:
            await asyncio.gather(*callback_tasks)

    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor_async for {actor.actor_name} failed:")
        LogUtil.exception(e)

# endregion


def _remove_file_process(session: Session, path: str, post_id: int, res_index: int, extra_data: any = None):
    os.remove(path)


def removeActorDownloadingFiles(session: Session, actor: ActorModel):
    traverseDownloadingFilesOfActor(session, actor, _remove_file_process)


def __hasDownloadingVideo_process(session: Session, path: str, post_id: int, res_index: int, extra_data: any = None) -> bool:
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return False
    if res.res_type == ResType.Image:
        return False
    return True


def hasDownloadingVideo(session: Session, actor: ActorModel) -> bool:
    return existDownloadingFilesOfActor(session, actor, __hasDownloadingVideo_process)


def __getResVideoInfo(session: Session, file_path: str, post_id: int, res_index: int) -> ResFileInfo:
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return None
    if res.res_type == ResType.Image:
        return None
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    return ResFileInfo(file_path=file_name, file_size=file_size, res_size=res.res_size)


def __getDownloadingFiles_Process(session: Session, file, post_id, res_index, ret: list[ResFileInfo]):
    # print(file)
    info = __getResVideoInfo(session, file, post_id, res_index)
    if info is not None:
        ret.append(info)


def getDownloadingFilesOfActor(session: Session, actor: ActorModel) -> list[ResFileInfo]:
    ret = []
    traverseDownloadingFilesOfActor(
        session, actor, __getDownloadingFiles_Process, ret)
    return ret


def _remove_file_percent_process(session: Session, file_path: str, post_id: int, res_index: int, percent: float):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Image:
        return
    file_size = os.path.getsize(file_path)
    if file_size <= res.res_size * percent:
        os.remove(file_path)


def removeDownloadingFilesOfActor(session: Session, actor: ActorModel, percent: float):
    if percent >= 1:
        traverseDownloadingFilesOfActor(session, actor, _remove_file_process)
    else:
        traverseDownloadingFilesOfActor(
            session, actor, _remove_file_percent_process, percent)


def _get_downloading_video_stats_process(session: Session, file, post_id, res_index, ret: dict[int, DownloadingVideoStats]):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Image:
        return
    post = res.post
    if post.actor_id not in ret:
        actor = post.actor
        actor_abstract = ActorAbstract(
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_group_id=actor.actor_group_id
        )
        ret[post.actor_id] = DownloadingVideoStats(
            actor_abstract=actor_abstract
        )
    ret[post.actor_id].add_info(os.path.getsize(file), res.res_size)


def get_downloading_video_stats(session: Session) -> list[DownloadingVideoStats]:
    ret_map: dict[int, DownloadingVideoStats] = {}
    traverseDownloadingFiles(
        session, _get_downloading_video_stats_process, ret_map)
    return list(ret_map.values())


def _rename_actor_file_process(session: Session, path: str, post_id: int, res_index: int, extra_data: any = None):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Image:
        return
    if res.res_width == 0 or res.res_height == 0 or res.res_duration == 0:
        return
    actor_folder, file_name = os.path.split(path)
    if DirUtil.hasPrefix(file_name):
        return
    new_file_name = f"{DirUtil.getPrefix(res.res_width >= res.res_height)}_{file_name}"
    os.rename(path, os.path.join(actor_folder, new_file_name))


def rename_actor_videos(session: Session, actor: ActorModel):
    traverseDownloadedFilesOfActor(session, actor, _rename_actor_file_process)


def _remove_by_dir_process(session: Session, path: str, post_id: int, res_index: int, is_landscape: bool):
    # 必须是已经rename过的才删除，防止误删
    base_name = os.path.basename(path)
    if not DirUtil.checkPrefix(base_name, is_landscape):
        return

    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return

    res.setState(ResState.Del)
    os.remove(path)


def remove_by_dir(session, actor: ActorModel, is_landscape: bool):
    traverseDownloadedFilesOfActor(
        session, actor, _remove_by_dir_process, is_landscape)
    ActorLogCtrl.addActorLog(
        session, actor.actor_id, ActorLogType.ClearFolder, DirUtil.getDirName(is_landscape))
    return


def _remove_thumbnail_image_process(session: Session, path: str, post_id: int, res_index: int, thumbnail_folder: str):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Video:
        return
    try:
        os.remove(os.path.join(thumbnail_folder, res.res_url_info.file_name))
    except FileNotFoundError:
        pass


def _remove_empty_thumbnail_image(thumbnail_folder: str):
    with os.scandir(thumbnail_folder) as it:
        for entry in it:
            if not entry.is_file():
                continue
            if os.path.getsize(entry.path) > 0:
                continue
            os.remove(entry.path)


def remove_thumbnail_images(session: Session, actor: ActorModel):
    thumbnail_folder = Configs.formatActorThumbnailFolderPath(
        actor.actor_id, actor.actor_name)
    traverseDownloadedFilesOfActor(
        session, actor, _remove_thumbnail_image_process, thumbnail_folder)
    _remove_empty_thumbnail_image(thumbnail_folder)


def _add_size_process(_0: Session, file: str, _1: int, _2: int, sum: list[int]):
    if os.path.exists(file):
        sum[0] += os.path.getsize(file)


def getTotalDownloadingSize(session: Session) -> int:
    sum = [0]
    traverseDownloadingFiles(session, _add_size_process, sum)
    return sum[0]


def __remove_outdated_process(session: Session, file_path: str, post_id: int, res_index: int, extra_data: any = None):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res.res_state == ResState.Del:
        LogUtil.info(f"remove downloading file {file_path}")
        os.remove(file_path)


def removeOutdatedFiles(session: Session):
    traverseDownloadingFiles(session, __remove_outdated_process)
