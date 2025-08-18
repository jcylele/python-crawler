import os
import re
import ffmpeg
from math import floor
from typing import Callable
from sqlalchemy.orm import Session

import Configs
from Consts import ResType
from Ctrls import ResCtrl
from Models.ActorModel import ActorModel
from Models.PostModel import PostModel
from Utils import LogUtil
from routers.web_data import DownloadingVideoStats, ResFileInfo

# region downloading files


def traverseDownloadedFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int], None]):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    for root, _, files in os.walk(actor_folder):
        for file in files:
            match_obj = re.match(r'^(\d+)_(\d+)\.\w+$', file)
            if match_obj is None:
                continue
            post_id = int(match_obj.group(1))
            res_index = int(match_obj.group(2))
            callback(session, os.path.join(root, file), post_id, res_index)


def traverseDownloadingFiles(session: Session, callback: Callable[[Session, str, int, int], None]):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file)
                if match_obj is None:
                    continue
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))
                callback(session, os.path.join(root, file), post_id, res_index)
    except Exception as e:
        pass


def traverseDownloadingFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int], None]):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file)
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
                callback(session, os.path.join(root, file), post_id, res_index)
    except Exception as e:
        LogUtil.error(
            f"traverseDownloadingFilesOfActor {actor.actor_name} failed, get {type(e)} {e.args}")


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
    ret = []
    traverseDownloadingFilesOfActor(
        session, actor, lambda _1, file, _2, _3: os.remove(file))
    return ret


def removeDownloadingFilesOfActor(session: Session, actor: ActorModel):
    ret = []
    traverseDownloadingFilesOfActor(
        session, actor, lambda _1, file, _2, _3: os.remove(file))
    return ret


def _get_downloading_video_stats_process(session: Session, file, post_id, res_index, ret: dict[int, DownloadingVideoStats]):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    if res.res_type == ResType.Image:
        return
    actor = res.post.actor
    if actor.actor_id not in ret:
        ret[actor.actor_id] = DownloadingVideoStats(
            actor.actor_id, actor.actor_name)
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
        LogUtil.error(f"get media info failed, get {type(e)} {e.args}")
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
