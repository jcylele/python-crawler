# PostModel related operations
import os

from sqlalchemy import select, ScalarResult, func
from sqlalchemy.orm import Session, Query

from Ctrls import FileInfoCacheCtrl, DbCtrl
from Models.BaseModel import PostModel, ResState, ActorModel
from routers.web_data import PostConditionForm, ActorPostInfo


def getPost(session: Session, post_id: int) -> PostModel:
    """
    get a post record by its id
    """
    return session.get(PostModel, post_id)


def getPostCount(session: Session, actor_id: int, completed: bool) -> int:
    _query = session.query(PostModel) \
        .where(PostModel.actor_id == actor_id) \
        .where(PostModel.completed == completed)
    return DbCtrl.queryCount(_query)


def getMaxPostId(session: Session, actor_id: int) -> int:
    _query = session.query(func.max(PostModel.post_id)) \
        .where(PostModel.actor_id == actor_id)
    result = session.execute(_query).fetchone()
    return result[0] or 0


def addPost(session: Session, actor_id: int, post_id: int):
    """
    add a post record
    """
    post = PostModel()
    post.post_id = post_id
    post.actor_id = actor_id
    session.add(post)
    session.flush()


def batchSetResStates(session: Session, actor_id: int, state: ResState):
    FileInfoCacheCtrl.RemoveCachedFileSizes(actor_id)
    # uncompleted post has no res in db
    stmt = (
        select(PostModel)
        .where(PostModel.actor_id == actor_id)
        .where(PostModel.completed == True)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        for res in post.res_list:
            res.setState(state)


# set current downloaded res(file exists) to del
def removeCurrentResFiles(session: Session, actor_id: int):
    # remove cache first, prevent update to cache
    FileInfoCacheCtrl.RemoveCachedFileSizes(actor_id)
    # uncompleted post has no res in db
    stmt = (
        select(PostModel)
        .where(PostModel.actor_id == actor_id)
        .where(PostModel.completed == True)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        for res in post.res_list:
            if os.path.exists(res.filePath()):
                res.setState(ResState.Del)


def filterQuery(_query: Query, form: PostConditionForm) -> Query:
    # actor_name
    if form.actor_id != 0:
        _query = _query.where(PostModel.actor_id == form.actor_id)
    # post_id_prefix
    if len(form.post_id_prefix) > 0:
        _query = _query.where(PostModel.post_id.like(f"{form.post_id_prefix}%"))
    # has_comment
    if form.has_comment:
        _query = _query.where(PostModel.comment != "")
    return _query


def getPostCountList(session: Session, form: PostConditionForm):
    _query = session.query(
        PostModel.actor_id,
        func.count(PostModel.post_id)
    ).group_by(PostModel.actor_id)
    _query = filterQuery(_query, form)
    result = session.execute(_query).fetchall()
    response = []
    for data in result:
        info = ActorPostInfo()
        info.actor_id = data[0]
        info.post_count = data[1]
        actor = session.get(ActorModel, info.actor_id)
        info.actor_name = actor.actor_name

        response.append(info)
    return response


def getFilteredPosts(session: Session, form: PostConditionForm) -> ScalarResult[PostModel]:
    _query = session.query(PostModel)
    _query = filterQuery(_query, form)
    # _query = _query.order_by(PostModel.actor_name)
    # _query = _query.order_by(desc(PostModel.post_id))
    return session.scalars(_query)


def setPostComment(session: Session, post_id: int, comment: str):
    post = getPost(session, post_id)
    if post is None:
        return
    post.comment = comment


def getNewPosts(session: Session, actor_id: int, last_post_id: int) -> ScalarResult[PostModel]:
    _query = session.query(PostModel) \
        .where(PostModel.actor_id == actor_id) \
        .where(PostModel.post_id > last_post_id)
    return session.scalars(_query)
