# PostModel related operations

from sqlalchemy import ScalarResult, func, select, update, Select, exists, or_
from sqlalchemy.orm import Session

from Consts import ResState, ResType
from Ctrls import ActorFileCtrl
from Models.ActorModel import ActorModel
from Models.ModelInfos import PostInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Utils import PyUtil
from routers.web_data import PostFilterForm
from routers.schemas_others import ActorPostInfo


def getPost(session: Session, post_id: int) -> PostModel:
    """
    get a post record by its id
    """
    return session.get(PostModel, post_id)


def getMaxPostId(session: Session, actor_id: int) -> int:
    _query = select(func.max(PostModel.post_id)) \
        .where(PostModel.actor_id == actor_id)
    result = session.scalar(_query)
    return result or 0


def addPost(session: Session, actor_id: int, post_info: PostInfo):
    """
    add a post record
    """
    post = PostModel()
    post.post_id = post_info.post_id
    post.post_id_str = post_info.post_id_str
    post.actor_id = actor_id
    post.has_thumbnail = post_info.has_thumbnail
    session.add(post)
    session.flush()


def batchSetResStates(session: Session, actor_id: int, state: ResState):
    _query = (update(ResModel)
              .where(ResModel.post_id == PostModel.post_id)
              .where(PostModel.actor_id == actor_id)
              .values(res_state=state))
    session.execute(_query)
    session.flush()
    # manually delete
    ActorFileCtrl.deleteActorFileInfo(actor_id)


# set current downloaded res(file exists) to del
def removeCurrentResFiles(session: Session, actor_id: int):
    _query = (update(ResModel)
              .where(ResModel.post_id == PostModel.post_id)
              .where(PostModel.actor_id == actor_id)
              .where(ResModel.res_state == ResState.Down)
              .values(res_state=ResState.Del))
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
        actor = session.get(ActorModel, data[0])
        info = ActorPostInfo(
            actor_id=data[0], actor_name=actor.actor_name, post_count=data[1])
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
    post = getPost(session, post_id)
    if not post:
        return
    post.comment = real_comment


def getPostsOfActor(session: Session, actor_id: int, last_post_id: int = 0, only_complete: bool = False) -> ScalarResult[PostModel]:
    _query = (select(PostModel)
              .where(PostModel.actor_id == actor_id))
    if last_post_id > 0:
        _query = _query.where(PostModel.post_id > last_post_id)
    if only_complete:
        _query = _query.where(PostModel.completed == True)
    _query = _query.order_by(PostModel.has_thumbnail,
                             PostModel.post_id.desc())
    return session.scalars(_query)


def getPostsToFixVideoUrls(session: Session, actor_id: int) -> ScalarResult[PostModel]:
    # 创建一个子查询来检查是否存在 res_type 为 Video 的 ResModel
    video_res_subquery = (
        select(1)
        .where(ResModel.post_id == PostModel.post_id)
        .where(ResModel.res_type == ResType.Video)
    )

    _query = (select(PostModel)
              .where(PostModel.actor_id == actor_id)
              .where(PostModel.completed == True)
              .where(exists(video_res_subquery))
              .order_by(PostModel.last_fetch_time.is_(None).desc(),
                        PostModel.last_fetch_time,
                        PostModel.post_id))
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
