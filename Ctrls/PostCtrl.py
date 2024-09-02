# PostModel related operations
import os

from sqlalchemy import select, ScalarResult, func
from sqlalchemy.orm import Session, Query

from Ctrls import FileInfoCacheCtrl, DbCtrl
from Models.BaseModel import PostModel, ResState
from routers.web_data import PostConditionForm, PostCommentForm


def getPost(session: Session, post_id: int) -> PostModel:
    """
    get a post record by its id
    """
    return session.get(PostModel, post_id)


def getPostCount(session: Session, actor_name: str, completed: bool) -> int:
    _query = session.query(PostModel) \
        .where(PostModel.actor_name == actor_name) \
        .where(PostModel.completed == completed)
    return DbCtrl.queryCount(_query)


def getMaxPostId(session: Session, actor_name: str) -> int:
    _query = session.query(func.max(PostModel.post_id)) \
        .where(PostModel.actor_name == actor_name)
    result = session.execute(_query).fetchone()
    return result[0] or 0


def addPost(session: Session, actor_name: str, post_id: int):
    """
    add a post record
    """
    post = PostModel()
    post.post_id = post_id
    post.actor_name = actor_name
    session.add(post)
    session.flush()


def batchSetResStates(session: Session, actor_name: str, state: ResState):
    FileInfoCacheCtrl.RemoveCachedFileSizes(actor_name)
    # uncompleted post has no res in db
    stmt = (
        select(PostModel)
            .where(PostModel.actor_name == actor_name)
            .where(PostModel.completed == True)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        for res in post.res_list:
            res.setState(state)


# set current downloaded res(file exists) to del
def removeCurrentResFiles(session: Session, actor_name: str):
    FileInfoCacheCtrl.RemoveCachedFileSizes(actor_name)
    # uncompleted post has no res in db
    stmt = (
        select(PostModel)
            .where(PostModel.actor_name == actor_name)
            .where(PostModel.completed == True)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        for res in post.res_list:
            if os.path.exists(res.filePath()):
                res.setState(ResState.Del)


def filterQuery(_query: Query, form: PostConditionForm) -> Query:
    # actor_name
    if form.actor_name is not None and len(form.actor_name) > 0:
        _query = _query.where(PostModel.actor_name == form.actor_name)
    # post_id_prefix
    if len(form.post_id_prefix) > 0:
        _query = _query.where(PostModel.post_id.like(f"{form.post_id_prefix}%"))
    # has_comment
    if form.has_comment:
        _query = _query.where(PostModel.comment != "")
    return _query


def getFilteredActors(session: Session, form: PostConditionForm):
    _query = session.query(
        PostModel.actor_name,
        func.count(PostModel.post_id)
    ).group_by(PostModel.actor_name)
    _query = filterQuery(_query, form)
    result = session.execute(_query).fetchall()
    response = []
    for data in result:
        response.append({
            'actor_name': data[0],
            'post_count': data[1],
        })
    return response


def getFilteredPosts(session: Session, form: PostConditionForm) -> ScalarResult[PostModel]:
    _query = session.query(PostModel)
    _query = filterQuery(_query, form)
    # _query = _query.order_by(PostModel.actor_name)
    # _query = _query.order_by(desc(PostModel.post_id))
    return session.scalars(_query)


def setPostComment(session: Session, form: PostCommentForm):
    post = getPost(session, form.post_id)
    if post is None:
        return
    post.comment = form.comment


def getNewPosts(session: Session, actor_name: str, last_post_id: int) -> ScalarResult[PostModel]:
    _query = session.query(PostModel) \
        .where(PostModel.actor_name == actor_name) \
        .where(PostModel.post_id > last_post_id)
    return session.scalars(_query)
