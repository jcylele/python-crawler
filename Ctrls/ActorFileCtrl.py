import os
import re

from sqlalchemy import delete, exists, insert, select, func, case, event
from sqlalchemy.orm import Session

import Configs
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorModel import ActorModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Consts import ResType
from Utils import LogUtil

__dirty_actors = set()


def __insert_actor_file_info(session, actor_id: int):
    # 构建 SELECT 语句
    select_stmt = select(
        # 固定值
        PostModel.actor_id.label('actor_id'),
        ResModel.res_state.label('res_state'),
        # 统计总大小
        func.sum(ResModel.res_size).label('res_size'),
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
    ).where(
        PostModel.actor_id == actor_id
    ).group_by(
        ResModel.res_state
    )

    # 构建 INSERT 语句
    insert_stmt = insert(ActorFileInfoModel).from_select(
        ['actor_id', 'res_state', 'res_size', 'img_count', 'video_count'],
        select_stmt
    )

    # 执行插入
    session.execute(insert_stmt)


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


def __deleteActorFileInfo(session: Session, actor_id: int):
    LogUtil.info(f"delete single actor: {actor_id}")
    stmt = delete(ActorFileInfoModel).where(
        ActorFileInfoModel.actor_id == actor_id)
    session.execute(stmt)


def ensureActorFileInfo(session: Session, actor_id: int, flush: bool = True):
    if actor_id in __dirty_actors:
        __deleteActorFileInfo(session, actor_id)
        __dirty_actors.remove(actor_id)
    elif __has_actor_file_info(session, actor_id):
        return
    __insert_actor_file_info(session, actor_id)
    if flush:
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
    LogUtil.info(f"delete by posts: {related_posts}")
    affected_actors = getActorsByPosts(session, related_posts)
    for actor_id in affected_actors:
        __dirty_actors.add(actor_id)
    # deleteActorFileInfo(session, set(affected_actors))


def RemoveDownloadingFiles(session: Session, actor: ActorModel):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file)
                if match_obj is None:
                    continue
                actor_name = match_obj.group(1)
                post_id = int(match_obj.group(2))
                if actor_name != actor.actor_name:
                    continue
                post = session.get(PostModel, post_id)
                if post is None:
                    continue
                if post.actor_id != actor.actor_id:
                    continue
                os.remove(os.path.join(root, file))
    except Exception as e:
        pass
