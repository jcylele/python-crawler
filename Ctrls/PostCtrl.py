# PostModel related operations

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

from Ctrls import ResCtrl
from Models.BaseModel import PostModel


def getPost(session: Session, post_id: int) -> PostModel:
    """
    get a post record by its id
    """
    return session.get(PostModel, post_id)


def addPost(session: Session, actor_name: str, post_id: int):
    """
    add a post record
    """
    post = PostModel()
    post.post_id = post_id
    post.actor_name = actor_name
    session.add(post)


def deleteAllPostOfActor(session: Session, actor_name: str):
    """
    delete all posts of an actor, along with all resource records
    :TODO not efficient enough, need optimization
    """
    stmt = (
        select(PostModel)
        .where(PostModel.actor_name == actor_name)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        ResCtrl.delAllRes(session, post.post_id)
        session.delete(post)
