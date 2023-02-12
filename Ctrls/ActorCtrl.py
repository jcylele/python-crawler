import json
import os

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

import Consts
import LogUtil
from Ctrls import PostCtrl, ResCtrl, CtrlUtil
from Models.BaseModel import ActorModel, ActorTag


def getActor(session: Session, actor_name: str) -> ActorModel:
    return session.get(ActorModel, actor_name)


def createActorFolder(actor_name: str):
    # 创建文件夹
    os.makedirs(Consts.formatActorFolderPath(actor_name), exist_ok=True)


def addActor(session: Session, actor_name: str, tag: ActorTag = ActorTag.Init) -> ActorModel:
    actor = getActor(session, actor_name)
    if actor is not None:
        # LogUtil.debug(f"{actor_name} already exist")
        return actor

    createActorFolder(actor_name)
    actor = ActorModel(actor_name=actor_name, actor_tag=tag)
    session.add(actor)
    return actor


def delActor(session: Session, actor_name: str):
    actor = getActor(session, actor_name)
    if actor is None:
        return
    session.delete(actor)


def hasActor(session: Session, actor_name: str) -> bool:
    actor = getActor(session, actor_name)
    return actor is not None


def getActorsByTag(session: Session, tag: ActorTag) -> ScalarResult[ActorModel]:
    stmt = select(ActorModel).where(ActorModel.actor_tag == tag)
    return session.scalars(stmt)


def likeAllActors(session: Session):
    actor_list = getActorsByTag(session, ActorTag.Init)
    for actor in actor_list:
        # 文件夹还在代表喜欢
        if os.path.exists(Consts.formatActorFolderPath(actor.actor_name)):
            actor.actor_tag = ActorTag.Liked


def repairRecords(session: Session):
    """
    根据文件是否存在刷新记录
    """
    stmt = select(ActorModel).where(ActorModel.actor_tag != ActorTag.Dislike)
    actor_list: ScalarResult[ActorModel] = session.scalars(stmt)
    for actor in actor_list:
        # 已删代表不喜欢
        if not os.path.exists(Consts.formatActorFolderPath(actor.actor_name)):
            if actor.actor_tag == ActorTag.Init:
                actor.actor_tag = ActorTag.Dislike
            else:
                actor.actor_tag = ActorTag.Enough
            PostCtrl.deleteAllPostOfActor(session, actor.actor_name)


