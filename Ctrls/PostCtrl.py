from sqlalchemy import delete, select, ScalarResult
from sqlalchemy.orm import Session

from Ctrls import ResCtrl
from Models.BaseModel import PostModel


def getPost(session: Session, post_id: int) -> PostModel:
    return session.get(PostModel, post_id)


def addPost(session: Session, actor_name: str, post_id: int):
    post = PostModel()
    post.post_id = post_id
    post.actor_name = actor_name
    session.add(post)


def deleteAllPostOfActor(session: Session, actor_name: str):
    stmt = (
        select(PostModel)
        .where(PostModel.actor_name == actor_name)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        ResCtrl.delAllRes(session, post.post_id)
        session.delete(post)
