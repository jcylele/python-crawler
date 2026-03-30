# PostModel related operations

from datetime import datetime

from sqlalchemy import ScalarResult, Select, exists, func, or_, select, update
from sqlalchemy.orm import Session

from Consts import ResState, ResType
from Ctrls import ActorFileCtrl, CommonCtrl
from Models.ActorModel import ActorModel
from Models.ModelInfos import ActorInfo, PostInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from routers.schemas_others import ActorPostInfo
from routers.web_data import PostFilterForm
from Utils import PyUtil


def getMaxPostId(session: Session, actor_id: int) -> int:
    _query = select(func.max(PostModel.post_id)) \
        .where(PostModel.actor_id == actor_id)
    result = session.scalar(_query)
    return result or 0


def addPost(session: Session, actor_info: ActorInfo, post_info: PostInfo):
    """
    add a post record
    """
    post = PostModel()
    post.post_id = post_info.post_id
    post.post_id_str = post_info.post_id_str
    post.has_thumbnail = post_info.has_thumbnail
    post.actor_id = actor_info.actor_id
    post.scan_version = actor_info.post_scan_version
    session.add(post)
    session.flush()


def batchSetResStates(session: Session, actor_id: int, old_state: ResState, new_state: ResState):
    _query = (update(ResModel)
              .where(ResModel.post_id == PostModel.post_id)
              .where(PostModel.actor_id == actor_id)
              .where(ResModel.res_state == old_state)
              .values(res_state=new_state))
    session.execute(_query)
    session.flush()
    # manually delete
    ActorFileCtrl.deleteActorFileInfo(actor_id)


def filterQuery(_query: Select, form: PostFilterForm) -> Select:
    # actor
    if form.actor_id != 0:
        _query = _query.where(PostModel.actor_id == form.actor_id)
    # post_id_prefix
    if len(form.post_id_prefix) > 0:
        _query = _query.where(or_(
            PostModel.post_id_str.like(f"{form.post_id_prefix}%"),
            PostModel.post_id_str.like(f"DM{form.post_id_prefix}%")
        ))
    # comment
    if form.has_comment:
        _query = _query.where(PostModel.has_comment == True)
        comment = form.comment.strip()
        if comment:
            _query = _query.where(PostModel.comment.like(f"%{comment}%"))

    return _query


def getPostCountList(session: Session, form: PostFilterForm) -> list[ActorPostInfo]:
    _query = select(
        PostModel.actor_id,
        func.count(PostModel.post_id)
    ).group_by(PostModel.actor_id)
    _query = filterQuery(_query, form)
    result = session.execute(_query).fetchall()
    response = []
    for data in result:
        actor = CommonCtrl.getActor(session, data[0])
        info = ActorPostInfo(
            actor_id=actor.actor_id, actor_name=actor.actor_name, post_count=data[1])
        response.append(info)
    return response


def getFilteredPosts(session: Session, form: PostFilterForm) -> list[PostModel]:
    _query = select(PostModel)
    _query = filterQuery(_query, form)
    # _query = _query.order_by(PostModel.actor_name)
    # _query = _query.order_by(desc(PostModel.post_id))
    return list(session.scalars(_query))


def setPostComment(session: Session, post_id: int, comment: str):
    real_comment = PyUtil.stripToNone(comment)
    update_query = update(PostModel).where(
        PostModel.post_id == post_id).values(comment=real_comment)
    session.execute(update_query)
    session.flush()


def getPostsOfActor(session: Session, actor_id: int, only_complete: bool = False) -> ScalarResult[PostModel]:
    _query = (select(PostModel)
              .where(PostModel.actor_id == actor_id))
    if only_complete:
        _query = _query.where(PostModel.completed == True)
    _query = _query.order_by(PostModel.has_thumbnail,
                             PostModel.post_id.desc())
    return session.scalars(_query)


def getPostsToFixVideoUrls(session: Session, actor_id: int, end_date: datetime) -> ScalarResult[PostModel]:
    # 创建一个子查询来检查是否存在 res_type 为 Video 的 ResModel
    video_res_subquery = (
        select(1)
        .where(ResModel.post_id == PostModel.post_id)
        .where(ResModel.res_type == ResType.Video)
    )

    _query = (select(PostModel)
              .where(PostModel.actor_id == actor_id)
              .where(PostModel.completed == True)
              .where(PostModel.last_fetch_time is not None)
              .where(PostModel.last_fetch_time < end_date)
              .where(exists(video_res_subquery)))
    return session.scalars(_query)


def getPostCountsOfActor(session: Session, actor_id: int) -> tuple[int, int]:
    _query = (select(PostModel.completed, func.count(PostModel.post_id))
              .where(PostModel.actor_id == actor_id)
              .group_by(PostModel.completed))
    result = session.execute(_query).fetchall()
    completed_count = 0
    uncompleted_count = 0
    for completed, count in result:
        if completed:
            completed_count = count
        else:
            uncompleted_count = count
    return completed_count, uncompleted_count


def hasMissingPosts(session: Session, actor_id: int, scan_version: int) -> bool:
    """
    Check if there are any posts with scan_version less than the actor's post_scan_version
    """
    stmt = (select(1)
            .where(PostModel.actor_id == actor_id)
            .where(PostModel.scan_version < scan_version).limit(1))
    return session.scalar(stmt) is not None


def refreshHasMissingPosts(session: Session):
    """
    Refresh the has_missing_posts flag for all actors
    """
    stmt = update(ActorModel).values(
        has_missing_posts=exists(
            select(1)
            .where(PostModel.actor_id == ActorModel.actor_id)
            .where(PostModel.scan_version < ActorModel.post_scan_version)
        )
    )
    session.execute(stmt)
    session.flush()
