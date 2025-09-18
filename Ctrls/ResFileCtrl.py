import asyncio
import os
import re
from typing import Any, Coroutine
import ffmpeg
from math import floor
from collections.abc import Callable
from sqlalchemy.orm import Session

import Configs
from Consts import ResType
from Ctrls import ResCtrl
from Models.ActorModel import ActorModel
from Models.PostModel import PostModel
from Utils import LogUtil
from routers.schemas_others import ResFileInfo, DownloadingVideoStats
# region downloading files


def traverseDownloadedFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int], None]):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)

    with os.scandir(actor_folder) as it:
        for entry in it:
            if entry.is_dir():
                continue
            match_obj = re.match(r'^(\d+)_(\d+)\.\w+$', entry.name)
            if match_obj is None:
                continue
            post_id = int(match_obj.group(1))
            res_index = int(match_obj.group(2))
            callback(session, entry.path, post_id, res_index)


def traverseDownloadingFiles(session: Session, callback: Callable[[Session, str, int, int], None]):
    download_folder = Configs.formatTmpFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', entry.name)
                if match_obj is None:
                    continue
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))
                callback(session, entry.path, post_id, res_index)
    except Exception as e:
        LogUtil.error(f"traverseDownloadingFiles failed, get Error")
        LogUtil.exception(e)
        pass


def traverseDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int], None]):
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
                callback(session, entry.path, post_id, res_index)
    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor {actor.actor_name} failed, get error")
        LogUtil.exception(e)


async def traverseDownloadingFilesOfActor_async(session: Session, actor: ActorModel,
                                                callback: Callable[[Session, str, int, int], Coroutine[Any, Any, None]]):
    """
    traverseDownloadingFilesOfActor 的异步版本。
    它使用线程池执行器来运行以避免阻塞事件循环。
    """

    def _walk_and_get_files(folder_path: str):
        # 这个函数在一个单独的线程中运行。
        try:
            file_names = []
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_file():
                        file_names.append(entry.name)
            return file_names
        except Exception as e:
            LogUtil.error(f"Error in traverseDownloadingFilesOfActor:")
            LogUtil.exception(e)
            return []

    download_folder = Configs.formatTmpFolderPath()
    loop = asyncio.get_running_loop()

    try:
        # 在默认的线程池执行器中运行阻塞的逻辑
        all_file_names = await loop.run_in_executor(None, _walk_and_get_files, download_folder)

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
                    download_folder, file_name), post_id, res_index)
            )

        # 并发执行所有回调任务
        if callback_tasks:
            await asyncio.gather(*callback_tasks)

    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor_async for {actor.actor_name} failed:")
        LogUtil.exception(e)


def removeDownloadingFiles(session: Session, actor: ActorModel):
    traverseDownloadingFilesOfActor(
        session, actor, lambda _1, file, _2, _3: os.remove(file))


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
    traverseDownloadingFilesOfActor(session, actor, lambda session, file, post_id,
                                    res_index: __getDownloadingFiles_Process(session, file, post_id, res_index, ret))
    return ret


def removeDownloadingFilesOfActor(session: Session, actor: ActorModel):
    traverseDownloadingFilesOfActor(
        session, actor, lambda _1, file, _2, _3: os.remove(file))


def _get_downloading_video_stats_process(session: Session, file, post_id, res_index, ret: dict[int, DownloadingVideoStats]):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Image:
        return
    actor = res.post.actor
    if actor.actor_id not in ret:
        ret[actor.actor_id] = DownloadingVideoStats(
            actor_id=actor.actor_id,
            actor_name=actor.actor_name
        )
    ret[actor.actor_id].add_info(os.path.getsize(file), res.res_size)


def get_downloading_video_stats(session: Session) -> list[DownloadingVideoStats]:
    ret_map: dict[int, DownloadingVideoStats] = {}
    traverseDownloadingFiles(session, lambda _1, file, post_id, res_index: _get_downloading_video_stats_process(
        session, file, post_id, res_index, ret_map))
    return list(ret_map.values())

# endregion

# region file info fetch / rename


def get_media_info(file_path) -> tuple[int, int, int]:
    """获取视频/图片文件的基本信息"""
    try:
        # 获取视频流信息
        probe = ffmpeg.probe(file_path)
        streams = probe['streams']
        video_stream = None
        # 获取视频流
        for stream in streams:
            codec_type = stream.get('codec_type')
            if codec_type == 'video' or codec_type == 'image':
                video_stream = stream
                break
        # 没有视频流
        if video_stream is None:
            return 0, 0, 0
        # 基本信息
        width = int(video_stream['width'])  # 宽度
        height = int(video_stream['height'])  # 高度
        duration = floor(float(probe['format'].get('duration', 0)))

        return width, height, duration
    except Exception as e:
        LogUtil.error(f"get media info failed")
        LogUtil.exception(e)
        return 0, 0, 0


def rename_actor_files(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    for file in os.listdir(actor_folder):
        match_obj = re.match(r'^(\d+)_(\d+)\.\w+$', file)
        if match_obj is None:
            continue
        post_id = int(match_obj.group(1))
        res_index = int(match_obj.group(2))
        res = ResCtrl.getResByIndex(session, post_id, res_index)
        if res is None:
            continue
        if res.res_type == ResType.Image:
            continue
        if res.res_width == 0 or res.res_height == 0 or res.res_duration == 0:
            continue
        prefix = res.res_width >= res.res_height and "l" or "p"
        new_file_name = f"{prefix}_{match_obj.group(0)}"
        os.rename(os.path.join(actor_folder, file),
                  os.path.join(actor_folder, new_file_name))

# endregion
