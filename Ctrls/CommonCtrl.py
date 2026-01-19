"""
some commonly used get functions, avoid recursive calls
"""
from sqlalchemy.orm import Session

from Consts import ErrorCode
from Models.ActorModel import ActorModel
from Models.Exceptions import BusinessException
from Models.ModelInfos import ActorInfo
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from routers.schemas_others import ActorAbstract


def getActor(session: Session, actor_id: int) -> ActorModel:
    actor = session.get(ActorModel, actor_id)
    if actor is None:
        raise BusinessException(ErrorCode.ActorNotFound)
    return actor


def getActorInfo(session: Session, actor_id: int) -> ActorInfo:
    actor = getActor(session, actor_id)
    return ActorInfo(actor)


def getActorAbstract(session: Session, actor_id: int) -> ActorAbstract:
    actor = getActor(session, actor_id)
    return ActorAbstract(
        actor_id=actor_id,
        actor_name=actor.actor_name,
        actor_group_id=actor.actor_group_id
    )

def getPost(session: Session, post_id: int) -> PostModel:
    post = session.get(PostModel, post_id)
    if post is None:
        raise BusinessException(ErrorCode.PostNotFound)
    return post

def tryGetPost(session: Session, post_id: int) -> PostModel | None:
    return session.get(PostModel, post_id)

def getRes(session: Session, res_id: int) -> ResModel:
    res = session.get(ResModel, res_id)
    if res is None:
        raise BusinessException(ErrorCode.ResNotFound)
    return res
