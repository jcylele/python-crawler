"""
ResFileCtrl is responsible for traversing related files of the resources.
"""

import asyncio
import os
import re
from collections.abc import Callable
from typing import Any, Coroutine

from sqlalchemy.orm import Session

import Configs
from Consts import ActorLogType, ResState, ResType
from Ctrls import ActorLogCtrl, CommonCtrl, ResCtrl
from Models.ActorModel import ActorModel
from routers.schemas_others import DownloadingVideoStats, ResFileInfo
from Utils import DirUtil, LogUtil, PyUtil

# region traverse file functions


def traverseActorFolders(session: Session, callback: Callable[[Session, str, int, any], None], extra_data: any = None):
    with os.scandir(Configs.getRootFolder()) as it:
        try:
            for entry in it:
                if entry.is_file():
                    continue
                match_obj = re.match(r'^(.+)_(\d+)$', entry.name)
                if match_obj is None:
                    continue
                actor_id = int(match_obj.group(2))
                callback(session, entry.path, actor_id, extra_data)
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
    download_folder = Configs.formatDownloadingFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(\d+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                actor_id = int(match_obj.group(1))
                res_id = int(match_obj.group(3))
                callback(session, entry.path, actor_id, res_id, extra_data)
    except Exception as e:
        LogUtil.error(f"traverseDownloadingFiles failed, get Error")
        LogUtil.exception(e)
        pass


def existDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int, any], bool], extra_data: any = None) -> bool:
    download_folder = Configs.formatDownloadingFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(\d+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                actor_id = int(match_obj.group(1))
                res_id = int(match_obj.group(3))
                if actor_id != actor.actor_id:
                    continue
                if callback(session, entry.path, actor_id, res_id, extra_data):
                    return True
    except Exception as e:
        LogUtil.error(
            f"existDownloadingFilesOfActor {actor.actor_name} failed, get error")
        LogUtil.exception(e)

    return False


def traverseDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int, any], None], extra_data: any = None):
    download_folder = Configs.formatDownloadingFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(\d+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                actor_id = int(match_obj.group(1))
                res_id = int(match_obj.group(3))
                if actor_id != actor.actor_id:
                    continue
                callback(session, entry.path, actor_id, res_id, extra_data)
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
        download_folder = Configs.formatDownloadingFolderPath()
        all_file_names = os.listdir(download_folder)

        callback_tasks = []
        for file_name in all_file_names:
            match_obj = re.match(r'^(\d+)_(\d+)_(\d+)\.\w+$', file_name)
            if not match_obj:
                continue
            actor_id = int(match_obj.group(1))
            res_id = int(match_obj.group(3))
            if actor_id != actor.actor_id:
                continue

            # 创建一个异步回调任务
            callback_tasks.append(
                callback(session, os.path.join(
                    download_folder, file_name), actor_id, res_id, extra_data)
            )

        # 并发执行所有回调任务
        if callback_tasks:
            await asyncio.gather(*callback_tasks)

    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor_async for {actor.actor_name} failed:")
        LogUtil.exception(e)

# endregion


def _remove_file_process(session: Session, path: str, _1: int, _2: int, extra_data: any = None):
    os.remove(path)


def removeActorDownloadingFiles(session: Session, actor: ActorModel):
    traverseDownloadingFilesOfActor(session, actor, _remove_file_process)


def __hasDownloadingVideo_process(session: Session, path: str, _1: int, res_id: int, extra_data: any = None) -> bool:
    res = CommonCtrl.getRes(session, res_id)
    if res.res_type == ResType.Image:
        return False
    return True


def hasDownloadingVideo(session: Session, actor: ActorModel) -> bool:
    return existDownloadingFilesOfActor(session, actor, __hasDownloadingVideo_process)


def __getResVideoInfo(session: Session, file_path: str, res_id: int) -> ResFileInfo:
    res = CommonCtrl.getRes(session, res_id)
    if res.res_type == ResType.Image:
        return None
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    return ResFileInfo(file_path=file_name, file_size=file_size, res_size=res.res_size)


def __getDownloadingFiles_Process(session: Session, file, _1: int, res_id, ret: list[ResFileInfo]):
    info = __getResVideoInfo(session, file, res_id)
    if info is not None:
        ret.append(info)


def getDownloadingFilesOfActor(session: Session, actor: ActorModel) -> list[ResFileInfo]:
    ret = []
    traverseDownloadingFilesOfActor(
        session, actor, __getDownloadingFiles_Process, ret)
    return ret


def _remove_file_percent_process(session: Session, file_path: str, actor_id: int, res_id: int, percent: int):
    res = CommonCtrl.getRes(session, res_id)
    if res.res_type == ResType.Image:
        return
    file_size = os.path.getsize(file_path)
    if file_size * 100 <= res.res_size * percent:
        os.remove(file_path)


def removeDownloadingFiles(session: Session, actor_id: int, percent: int):
    if actor_id == 0:
        if percent == 100:
            traverseDownloadingFiles(session, _remove_file_process)
        else:
            traverseDownloadingFiles(
                session, _remove_file_percent_process, percent)
    else:
        actor = CommonCtrl.getActor(session, actor_id)
        if percent == 100:
            traverseDownloadingFilesOfActor(
                session, actor, _remove_file_process)
        else:
            traverseDownloadingFilesOfActor(
                session, actor, _remove_file_percent_process, percent)


def _get_downloading_video_stats_process(session: Session, file, actor_id, res_id, ret: dict[int, DownloadingVideoStats]):
    res = CommonCtrl.getRes(session, res_id)
    if res.res_type == ResType.Image:
        return
    if actor_id not in ret:
        actor_abstract = CommonCtrl.getActorAbstract(session, actor_id)
        ret[actor_id] = DownloadingVideoStats(
            actor_abstract=actor_abstract
        )
    ret[actor_id].add_info(os.path.getsize(file), res.res_size)


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
    actor_folder, file_name = os.path.split(path)
    if DirUtil.hasPrefix(file_name):
        return
    # media info is not set, set it
    if res.res_width == 0:
        if not res.setMediaInfo(PyUtil.get_media_info(path)):
            return
    # media has no width, skip
    if res.res_width == -1:
        return
    # rename file
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

    res.setState(ResState.Finished)
    os.remove(path)


def remove_by_dir(session, actor: ActorModel, is_landscape: bool):
    traverseDownloadedFilesOfActor(
        session, actor, _remove_by_dir_process, is_landscape)
    ActorLogCtrl.addActorLog(
        session, actor.actor_id, ActorLogType.ClearFolder, DirUtil.getDirName(is_landscape))
    return


def _remove_empty_thumbnail_image(thumbnail_folder: str):
    with os.scandir(thumbnail_folder) as it:
        for entry in it:
            if not entry.is_file():
                continue
            if os.path.getsize(entry.path) > 0:
                continue
            os.remove(entry.path)


def _add_size_process(_0: Session, file: str, _1: int, _2: int, sum: list[int]):
    if os.path.exists(file):
        sum[0] += os.path.getsize(file)


def getTotalDownloadingSize(session: Session) -> int:
    sum = [0]
    traverseDownloadingFiles(session, _add_size_process, sum)
    return sum[0]


def __remove_outdated_process(session: Session, file_path: str, _1: int, res_id: int, extra_data: any = None):
    res = CommonCtrl.getRes(session, res_id)
    if res.res_state == ResState.Finished:
        LogUtil.info(f"remove outdated downloading file {file_path}")
        os.remove(file_path)


def removeOutdatedFiles(session: Session):
    traverseDownloadingFiles(session, __remove_outdated_process)
