import os
import shutil
import threading
from pathlib import Path
from collections.abc import Iterable
from sqlalchemy import Select, delete, exists, select, func, case, event
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

import Configs
from Models.ModelInfos import ActorInfo
from Models.ActorModel import ActorModel
from Utils import PyUtil
from Utils.PyUtil import time_cost
from routers.schemas_others import ActorVideoInfo, ActorFileDetail, PostFetchTimeStats

from Ctrls import ActorLogCtrl, DbCtrl, PostCtrl, ResCtrl, ResFileCtrl
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Consts import ActorLogType, DateFormat, ResState, ResType
from Utils import LogUtil

_dirty_lock = threading.Lock()
_cleanup_timer: threading.Timer | None = None

__dirty_actor_ids = set()
__dirty_post_ids = set()

# region cleanup 10s after last change


def _dirty_cleanup_job():
    with DbCtrl.getSession() as session, session.begin():
        __process_dirty(session)


def _schedule_cleanup():
    global _cleanup_timer
    if _cleanup_timer:
        _cleanup_timer.cancel()
    _cleanup_timer = threading.Timer(10, _dirty_cleanup_job)
    _cleanup_timer.start()


def stop_cleanup_task():
    global _cleanup_timer
    if _cleanup_timer:
        _cleanup_timer.cancel()
        _cleanup_timer = None


def process_dirty_on_shutdown():
    stop_cleanup_task()
    _dirty_cleanup_job()

# endregion

# region actor file info model


def __build_basic_stmt() -> Select:
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
    rows = list(result)
    if not rows:
        return

    # 将 result 转换为字典列表
    insert_values = [
        {
            'actor_id': row.actor_id,
            'res_state': row.res_state,
            'img_size': row.img_size,
            'video_size': row.video_size,
            'img_count': row.img_count,
            'video_count': row.video_count
        } for row in rows
    ]

    if not insert_values:
        return

    # 构建 insert ... on duplicate key update 语句
    stmt = insert(ActorFileInfoModel).values(insert_values)
    update_stmt = stmt.on_duplicate_key_update(
        img_size=stmt.inserted.img_size,
        video_size=stmt.inserted.video_size,
        img_count=stmt.inserted.img_count,
        video_count=stmt.inserted.video_count
    )
    session.execute(update_stmt)
    session.flush()


def _build_single_stmt(actor_id: int) -> Select:
    return __build_basic_stmt().where(
        PostModel.actor_id == actor_id
    ).group_by(
        ResModel.res_state
    ).order_by(
        ResModel.res_state
    )


def __insert_actor_file_info(session, actor_id: int):
    # 构建 SELECT 语句
    select_stmt = _build_single_stmt(actor_id)

    result = session.execute(select_stmt)
    __insert_result(session, result)


def __build_batch_stmt(actor_ids: list[int]) -> Select:
    return __build_basic_stmt().where(
        PostModel.actor_id.in_(actor_ids)
    ).group_by(
        PostModel.actor_id,
        ResModel.res_state
    ).order_by(
        PostModel.actor_id,
        ResModel.res_state
    )


def __insert_batch_actor_file_info(session: Session, actor_ids: list[int]):
    # 构建 SELECT 语句
    select_stmt = __build_batch_stmt(actor_ids)

    result = session.execute(select_stmt)
    __insert_result(session, result)


def _get_actor_file_info(session: Session, actor_id: int) -> list[ActorFileInfoModel]:
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


def __deleteActorFileInfos(session: Session, actor_ids: set[int] | list[int]):
    stmt = delete(ActorFileInfoModel).where(
        ActorFileInfoModel.actor_id.in_(actor_ids))
    session.execute(stmt)
    session.flush()


def ensureActorFileInfo(session: Session, actor_id: int):
    __process_dirty(session)
    if __has_actor_file_info(session, actor_id):
        return
    __insert_actor_file_info(session, actor_id)
    session.flush()


def getActorFileInfo(session: Session, actor_id: int):
    ensureActorFileInfo(session, actor_id)
    return _get_actor_file_info(session, actor_id)


def deleteActorFileInfo(actor_id: int):
    with _dirty_lock:
        __dirty_actor_ids.add(actor_id)
        _schedule_cleanup()


def deleteActorFileInfos(actor_ids: Iterable[int]):
    with _dirty_lock:
        __dirty_actor_ids.update(actor_ids)
        _schedule_cleanup()


def __filter_actor_ids(session: Session, actor_ids: list[int]):
    """查询哪些actor_ids没有ActorFileInfoModel记录"""

    # 查询已存在的actor_ids
    existing_stmt = select(ActorFileInfoModel.actor_id).where(
        ActorFileInfoModel.actor_id.in_(actor_ids)
    )
    existing_ids = set(session.execute(existing_stmt).scalars().all())
    # LogUtil.info(f"existing actors: {existing_ids}")
    # 返回不存在的actor_ids
    missing_ids = [aid for aid in actor_ids if aid not in existing_ids]
    return missing_ids


def ensureBatchActorFileInfo(session: Session, actor_ids: list[int]):
    __process_dirty(session)
    if len(actor_ids) == 0:
        return
    missing_ids = __filter_actor_ids(session, actor_ids)
    if len(missing_ids) > 0:
        __insert_batch_actor_file_info(session, missing_ids)
        session.flush()


def __getActorsByPosts(session: Session, post_ids: set[int]):
    stmt = select(PostModel.actor_id.distinct()).where(
        PostModel.post_id.in_(post_ids))
    return session.execute(stmt).scalars()


def __process_dirty(session: Session):
    remove_actor_ids = set()
    with _dirty_lock:
        if len(__dirty_post_ids) > 0:
            affected_actors = __getActorsByPosts(session, __dirty_post_ids)
            for actor_id in affected_actors:
                __dirty_actor_ids.add(actor_id)
            __dirty_post_ids.clear()
        if len(__dirty_actor_ids) > 0:
            remove_actor_ids.update(__dirty_actor_ids)
            __dirty_actor_ids.clear()
            stop_cleanup_task()

    if len(remove_actor_ids) > 0:
        LogUtil.info(f"delete dirty actors: {remove_actor_ids}")
        __deleteActorFileInfos(session, remove_actor_ids)


@event.listens_for(Session, 'after_flush')
def __collect_dirty_posts(session, context):
    with _dirty_lock:
        post_added = False
        for obj in session.dirty:
            if isinstance(obj, ResModel):
                __dirty_post_ids.add(obj.post_id)
                post_added = True
        for obj in session.new:
            if isinstance(obj, ResModel):
                __dirty_post_ids.add(obj.post_id)
                post_added = True
        for obj in session.deleted:
            if isinstance(obj, ResModel):
                __dirty_post_ids.add(obj.post_id)
                post_added = True

        if post_added:
            _schedule_cleanup()

# endregion

# resources and files


@time_cost
def validate_all_file_info_new(session: Session) -> int:
    """
    全面检查ActorFileInfoModel，太耗时了，暂时弃用
    """
    __process_dirty(session)

    # 获取所有 actor_id
    stmt = select(ActorFileInfoModel.actor_id.distinct())
    all_actor_ids = list(session.scalars(stmt))
    if len(all_actor_ids) == 0:
        return 0

    BATCH_SIZE = 500  # 定义每个批次处理的 actor 数量
    all_unmatched_ids = set()
    # 分批处理所有 actor_id
    for i in range(0, len(all_actor_ids), BATCH_SIZE):
        batch_ids = all_actor_ids[i:i + BATCH_SIZE]
        # 为当前批次构建子查询 (与之前逻辑相同，但数据范围小得多)
        live_stats_sq = __build_batch_stmt(batch_ids).subquery('live_stats')

        # 对当前批次的数据进行 JOIN 和比较
        mismatched_ids_stmt = select(ActorFileInfoModel.actor_id.distinct()).where(
            ActorFileInfoModel.actor_id.in_(batch_ids)  # 只关注当前批次的缓存
        ).outerjoin(
            live_stats_sq,
            (ActorFileInfoModel.actor_id == live_stats_sq.c.actor_id) &
            (ActorFileInfoModel.res_state == live_stats_sq.c.res_state)
        ).where(
            # WHERE 条件筛选出所有不一致的数据
            # 使用 COALESCE 处理 live_stats 中可能因 JOIN 失败而产生的 NULL 值
            (ActorFileInfoModel.img_size != func.coalesce(live_stats_sq.c.img_size, 0)) |
            (ActorFileInfoModel.video_size != func.coalesce(live_stats_sq.c.video_size, 0)) |
            (ActorFileInfoModel.img_count != func.coalesce(live_stats_sq.c.img_count, 0)) |
            (ActorFileInfoModel.video_count != func.coalesce(live_stats_sq.c.video_count, 0)) |
            # 这种情况检查缓存中有，但实时统计中已经不存在的条目
            (live_stats_sq.c.actor_id == None)
        )

        unmatched_actor_ids = session.scalars(mismatched_ids_stmt).all()
        all_unmatched_ids.update(unmatched_actor_ids)

    # 对所有不匹配的ID进行处理
    if all_unmatched_ids:
        deleteActorFileInfos(all_unmatched_ids)

    return len(all_unmatched_ids)


def validateActorFileInfo(session: Session, actor_id: int) -> list[ActorFileInfoModel]:
    # delete
    with _dirty_lock:
        __dirty_actor_ids.add(actor_id)
    __process_dirty(session)
    # insert
    __insert_actor_file_info(session, actor_id)
    session.flush()
    # get
    return _get_actor_file_info(session, actor_id)


def getActorFileDetail(session: Session, actor_id: int) -> ActorFileDetail:
    actor = session.get(ActorModel, actor_id)
    res_info = getActorFileInfo(session, actor_id)
    # compute is_completed
    is_completed = True
    if actor.last_post_fetch_time is None or actor.completed_post_count != actor.total_post_count:
        is_completed = False
    if is_completed:
        for res in res_info:
            if res.res_state == ResState.Init and res.video_count > 0:
                is_completed = False
                break

    thumbnail_folder = Configs.formatActorThumbnailFolderPath(
        actor.actor_id, actor.actor_name)
    thumbnail_count = PyUtil.fileCount(thumbnail_folder)

    return ActorFileDetail(
        thumbnail_count=thumbnail_count,
        res_info=res_info,
        total_post_count=actor.total_post_count,
        unfinished_post_count=actor.current_post_count - actor.completed_post_count,
        finished_post_count=actor.completed_post_count,
        is_completed=is_completed
    )


def deleteAllRes(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        ResFileCtrl.removeActorDownloadingFiles(session, actor)

    PostCtrl.batchSetResStates(session, actor.actor_id, ResState.Del)


def clearActorFolder(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    if not os.path.exists(actor_folder):
        return
    # set res state according to file existence
    PostCtrl.removeCurrentResFiles(session, actor.actor_id)
    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.ClearFolder)
    # remove folder
    shutil.rmtree(actor_folder)
    # recreate folder
    createActorFolder(actor)


def getActorVideoStats(session: Session, actor_id: int) -> list[ActorVideoInfo]:
    landscape_info = ActorVideoInfo(is_landscape=True)
    portrait_info = ActorVideoInfo(is_landscape=False)
    stmt = select(
        ResModel
    ).join(
        PostModel, PostModel.post_id == ResModel.post_id
    ).where(
        PostModel.actor_id == actor_id,
        ResModel.res_state == ResState.Down,
        ResModel.res_type == ResType.Video
    )

    ret = session.scalars(stmt)
    for res in ret:
        if res.res_duration == 0:
            continue
        if res.res_width >= res.res_height:
            landscape_info.add_info(res.res_duration, res.res_size)
        else:
            portrait_info.add_info(res.res_duration, res.res_size)
    return [landscape_info, portrait_info]


def createActorFolder(actor: ActorInfo | ActorModel):
    actor_folder_path = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    os.makedirs(actor_folder_path, exist_ok=True)
    thumbnail_folder_path = Configs.formatActorThumbnailFolderPath(
        actor.actor_id, actor.actor_name)
    os.makedirs(thumbnail_folder_path, exist_ok=True)


def getPostFetchTimeStats(session: Session, actor_id: int) -> list[PostFetchTimeStats]:
    formatted_results: list[PostFetchTimeStats] = []
    # none count
    none_stmt = select(
        func.count(PostModel.post_id)
    ).where(
        PostModel.actor_id == actor_id,
        PostModel.last_fetch_time.is_(None)
    )
    none_count = session.scalar(none_stmt)
    if none_count and none_count > 0:
        formatted_results.append(PostFetchTimeStats(
            stat_date="",
            post_count=none_count
        ))
    # count by date
    stmt = select(
        func.date(PostModel.last_fetch_time),
        func.count(PostModel.post_id)
    ).where(
        PostModel.actor_id == actor_id,
        PostModel.last_fetch_time.isnot(None)
    ).group_by(
        func.date(PostModel.last_fetch_time)
    ).order_by(
        func.date(PostModel.last_fetch_time)
    )
    ret = session.execute(stmt)
    for stat_date, post_count in ret:
        formatted_results.append(PostFetchTimeStats(
            stat_date=PyUtil.datetime_format(stat_date, DateFormat.Date),
            post_count=post_count
        ))
    return formatted_results

# endregion
