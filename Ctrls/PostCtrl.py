# PostModel related operations

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

from Ctrls import ResCtrl
from Models.BaseModel import PostModel, ResState


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


def deleteAllFilesOfActor(session: Session, actor_name: str):
    stmt = (
        select(PostModel)
            .where(PostModel.actor_name == actor_name)
    )
    post_list: ScalarResult[PostModel] = session.scalars(stmt)
    for post in post_list:
        for res in post.res_list:
            if res.res_state == ResState.Down:
                res.res_state = ResState.Del

