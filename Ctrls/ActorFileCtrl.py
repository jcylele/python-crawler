import os
import re
from math import floor
import threading
from typing import Callable
import ffmpeg

from sqlalchemy import Select, delete, exists, select, func, case, event
from sqlalchemy.orm import Session

import Configs
from Ctrls import ResCtrl
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorModel import ActorModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Consts import ResType
from Utils import LogUtil
from routers.web_data import ResFileInfo

# 添加一个全局锁
_actor_file_info_lock = threading.Lock()

# region actor file info abstract

__dirty_actors = set()


def __build_basic_select_stmt() -> Select:
    return select(
        # 固定值
        PostModel.actor_id.label('actor_id'),
        ResModel.res_state.label('res_state'),
        # 统计总大小
        func.sum(case(
            (ResModel.res_type == ResType.Image, ResModel.res_size),
            else_=0
        )).label('img_size'),
        func.sum(case(
            (ResModel.res_type == ResType.Video, ResModel.res_size),
            else_=0
        )).label('video_size'),
        # 统计图片数量
        func.sum(
            case(
                (ResModel.res_type == ResType.Image, 1),
                else_=0
            )
        ).label('img_count'),
        # 统计视频数量
        func.sum(
            case(
                (ResModel.res_type == ResType.Video, 1),
                else_=0
            )
        ).label('video_count')
    ).join(
        PostModel,
        PostModel.post_id == ResModel.post_id
    )


def __insert_result(session: Session, result):
    if not result:
        return

   # 转换为ORM对象列表
    for row in result:
        actor_file_info = ActorFileInfoModel(
            actor_id=row.actor_id,
            res_state=row.res_state,
            img_size=row.img_size,
            video_size=row.video_size,
            img_count=row.img_count,
            video_count=row.video_count
        )
        # merge会自动处理插入或更新
        session.merge(actor_file_info)

    session.flush()


def __insert_actor_file_info(session, actor_id: int):
    # 构建 SELECT 语句
    select_stmt = __build_basic_select_stmt(
    ).where(
        PostModel.actor_id == actor_id
    ).group_by(
        ResModel.res_state
    )

    result = session.execute(select_stmt)
    __insert_result(session, result)


def __insert_batch_actor_file_info(session: Session, actor_ids: list[int]):
    # 构建 SELECT 语句
    select_stmt = __build_basic_select_stmt(
    ).where(
        PostModel.actor_id.in_(actor_ids)
    ).group_by(
        PostModel.actor_id,
        ResModel.res_state
    )

    result = session.execute(select_stmt)
    __insert_result(session, result)


def __get_actor_file_info(session: Session, actor_id: int) -> list[ActorFileInfoModel]:
    stmt = select(ActorFileInfoModel).where(
        ActorFileInfoModel.actor_id == actor_id
    )
    ret = session.execute(stmt).scalars()
    return list(ret)


def __has_actor_file_info(session: Session, actor_id: int):
    stmt = select(exists().where(
        ActorFileInfoModel.actor_id == actor_id
    ))
    return session.execute(stmt).scalar()


def __deleteSingleActorFileInfo(session: Session, actor_id: int):
    LogUtil.info(f"delete single actor: {actor_id}")
    stmt = delete(ActorFileInfoModel).where(
        ActorFileInfoModel.actor_id == actor_id)
    session.execute(stmt)


def __deleteDirtyActorFileInfos(session: Session):
    # LogUtil.info(f"delete dirty actors")
    stmt = delete(ActorFileInfoModel).where(
        ActorFileInfoModel.actor_id.in_(__dirty_actors))
    session.execute(stmt)
    session.flush()


def ensureActorFileInfo(session: Session, actor_id: int):
    with _actor_file_info_lock:
        if actor_id in __dirty_actors:
            __deleteSingleActorFileInfo(session, actor_id)
            __dirty_actors.remove(actor_id)
        elif __has_actor_file_info(session, actor_id):
            return
        __insert_actor_file_info(session, actor_id)
        session.flush()


def getActorFileInfo(session: Session, actor_id: int):
    ensureActorFileInfo(session, actor_id)
    return __get_actor_file_info(session, actor_id)


def deleteActorFileInfo(session: Session, actor_id: int):
    __dirty_actors.add(actor_id)


def clearAllActorFileInfo(session: Session):
    LogUtil.info(f"clear all actor file info")
    stmt = delete(ActorFileInfoModel)
    session.execute(stmt)
    __dirty_actors.clear()


def getActorsByPosts(session: Session, post_ids: set[int]):
    stmt = select(PostModel.actor_id.distinct()).where(
        PostModel.post_id.in_(post_ids))
    return session.execute(stmt).scalars()


def __filter_actor_ids(session: Session, actor_ids: list[int]):
    """查询哪些actor_ids没有ActorFileInfoModel记录"""
    if not actor_ids:
        return []

    # 查询已存在的actor_ids
    existing_stmt = select(ActorFileInfoModel.actor_id).where(
        ActorFileInfoModel.actor_id.in_(actor_ids)
    )
    existing_ids = set(session.execute(existing_stmt).scalars().all())
    LogUtil.info(f"existing actors: {existing_ids}")
    # 返回不存在的actor_ids
    missing_ids = [aid for aid in actor_ids if aid not in existing_ids]
    return missing_ids


def ensureBatchActorFileInfo(session: Session, actor_ids: list[int]):
    with _actor_file_info_lock:
        LogUtil.info(f"ensure actors: {actor_ids}")
        if len(__dirty_actors) > 0:
            LogUtil.info(f"delete dirty actors: {__dirty_actors}")
            __deleteDirtyActorFileInfos(session)
            __dirty_actors.clear()
        missing_ids = __filter_actor_ids(session, actor_ids)
        if len(missing_ids) == 0:
            return
        LogUtil.info(f"insert missing actors: {missing_ids}")
        __insert_batch_actor_file_info(session, missing_ids)
        session.flush()


@event.listens_for(Session, 'after_flush')
def update_actor_file_info_cache_batch(session, context):
    # 收集需要更新的 actor_id

    related_posts = set()
    for obj in session.dirty:
        if isinstance(obj, ResModel):
            related_posts.add(obj.post_id)
    for obj in session.new:
        if isinstance(obj, ResModel):
            related_posts.add(obj.post_id)
    for obj in session.deleted:
        if isinstance(obj, ResModel):
            related_posts.add(obj.post_id)

    if len(related_posts) == 0:
        return
    # LogUtil.info(f"delete by posts: {related_posts}")
    affected_actors = getActorsByPosts(session, related_posts)
    for actor_id in affected_actors:
        __dirty_actors.add(actor_id)
    # deleteActorFileInfo(session, set(affected_actors))

# endregion

# region downloading files

def traverseDownloadedFilesOfActor(session: Session, actor: ActorModel, callback: Callable[[Session, str, int, int], None]):
    actor_folder = Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)
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


def RemoveDownloadingFiles(session: Session, actor: ActorModel):
    traverseDownloadingFilesOfActor(
        session, actor, lambda session, file, post_id, res_index: os.remove(file))


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
    print(file)
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
        session, actor, lambda _, file, post_id, res_index: os.remove(file))
    return ret


# endregion


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
