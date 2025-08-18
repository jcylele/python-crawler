import os
import shutil
import threading
from typing import Union
from sqlalchemy import Select, delete, exists, select, func, case, event
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

import Configs
from Models.ActorInfo import ActorInfo
from Models.ActorModel import ActorModel
from routers.web_data import ActorFileDetail, ActorVideoInfo
from Ctrls import ActorLogCtrl, DbCtrl, PostCtrl, ResCtrl, ResFileCtrl
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Consts import ActorLogType, ResState, ResType
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
    LogUtil.info(f"delete dirty actors: {actor_ids}")
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


def deleteActorFileInfos(actor_ids: list[int]):
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
        __deleteActorFileInfos(session, list(remove_actor_ids))


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


def validate(session: Session, actor_id: int) -> bool:
    select_stmt = _build_single_stmt(actor_id)
    list1 = list(session.execute(select_stmt))
    list2 = _get_actor_file_info(session, actor_id)
    if len(list1) != len(list2):
        return False
    list1.sort(key=lambda x: x.res_state.value)
    list2.sort(key=lambda x: x.res_state.value)
    for i in range(len(list1)):
        if not list2[i].equal(list1[i]):
            return False
    return True

# endregion

# resources and files


def validate_all_file_info(session: Session) -> int:
    actor_ids = []
    stmt = select(ActorFileInfoModel.actor_id.distinct())
    for actor_id in session.scalars(stmt):
        if not validate(session, actor_id):
            actor_ids.append(actor_id)
    deleteActorFileInfos(actor_ids)
    return len(actor_ids)


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

    return {
        'res_info': res_info,
        'total_post_count': actor.total_post_count,
        'unfinished_post_count': actor.current_post_count - actor.completed_post_count,
        'finished_post_count': actor.completed_post_count,
        'is_completed': is_completed
    }


def __removeDeletedFile(session: Session, file_path: str, post_id: int, res_index: int):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res.res_state == ResState.Del:
        LogUtil.info(f"remove downloading file {file_path}")
        os.remove(file_path)


def removeOutdatedFiles(session: Session):
    ResFileCtrl.traverseDownloadingFiles(session, __removeDeletedFile)


def deleteAllRes(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        ResFileCtrl.removeDownloadingFiles(session, actor)

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
    landscape_info = ActorVideoInfo(True)
    portrait_info = ActorVideoInfo(False)
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
        if res.res_width >= res.res_height:
            landscape_info.add_info(res.res_duration, res.res_size)
        else:
            portrait_info.add_info(res.res_duration, res.res_size)
    return [landscape_info, portrait_info]


def createActorFolder(actor: Union[ActorInfo, ActorModel]):
    os.makedirs(Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name), exist_ok=True)

# endregion
