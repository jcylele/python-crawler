# ActorModel related operations

import os
import shutil

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

import Configs
from Ctrls import PostCtrl, DbCtrl, ResCtrl
from Models.BaseModel import ActorModel, ActorCategory, ActorTagRelationship


def getActor(session: Session, actor_name: str) -> ActorModel:
    """
    get record of the actor
    :return:
    """
    return session.get(ActorModel, actor_name)


def createActorFolder(actor_name: str):
    """
    create a folder for the actor
    :param actor_name:
    :return:
    """
    os.makedirs(Configs.formatActorFolderPath(actor_name), exist_ok=True)


def addActor(session: Session, actor_name: str) -> ActorModel:
    """
    create a record for the actor, skip if already exist
    :param session:
    :param actor_name:
    :return: actor record
    """
    actor = getActor(session, actor_name)
    if actor is not None:
        return actor

    createActorFolder(actor_name)
    actor = ActorModel(actor_name=actor_name)
    session.add(actor)

    return actor


def hasActor(session: Session, actor_name: str) -> bool:
    """
    check if actor already exist
    :param session:
    :param actor_name:
    :return: exist or not
    """
    actor = getActor(session, actor_name)
    return actor is not None


def getActorCount(session: Session, category: ActorCategory) -> int:
    _query = session.query(ActorModel)
    if category != ActorCategory.All:
        _query = _query.where(ActorModel.actor_category == category)
    return DbCtrl.queryCount(_query)


def getActorsByCategory(session: Session, category: ActorCategory, limit: int = 0, start: int = 0) -> ScalarResult[
    ActorModel]:
    """
    search actors by category
    """
    _query = session.query(ActorModel).order_by(ActorModel.actor_name)
    if category != ActorCategory.All:
        _query = _query.where(ActorModel.actor_category == category)
    if start != 0:
        _query = _query.offset(start)
    if limit != 0:
        _query = _query.limit(limit)
    return session.scalars(_query)


def removeTagFromActor(session: Session, actor_name: str, tag_id: int) -> ActorModel:
    actor = getActor(session, actor_name)
    for rel in actor.rel_tags:
        if rel.tag_id == tag_id:
            actor.rel_tags.remove(rel)
            session.delete(rel)
            break

    session.flush()
    return actor


def addTagsToActor(session: Session, actor_name: str, tag_list: list[int]) -> ActorModel:
    actor = getActor(session, actor_name)

    for tag_id in tag_list:
        relation = ActorTagRelationship()
        relation.tag_id = tag_id
        relation.actor_name = actor_name
        actor.rel_tags.append(relation)

    session.flush()
    return actor


__SwitchRemoveFiles = {
    ActorCategory.Init: {
        ActorCategory.Liked: False,
        ActorCategory.Dislike: True,
        ActorCategory.Enough: True,
    },
    ActorCategory.Liked: {
        ActorCategory.Init: False,
        ActorCategory.Dislike: True,
        ActorCategory.Enough: True,
    },
    ActorCategory.Dislike: {
        ActorCategory.Init: False,
    },
    ActorCategory.Enough: {
        ActorCategory.Init: False,
        ActorCategory.Liked: False,
        ActorCategory.Dislike: False,
    },
}


def changeActorCategory(session: Session, actor_name: str, new_category: ActorCategory) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.actor_category == new_category:
        return actor
    switch_map = __SwitchRemoveFiles.get(actor.actor_category)
    remove_files = switch_map.get(new_category)
    # unable to change
    if remove_files is None:
        return actor
    # remove files
    if remove_files:
        shutil.rmtree(Configs.formatActorFolderPath(actor.actor_name))
        PostCtrl.deleteAllFilesOfActor(session, actor.actor_name)
    # set field
    actor.actor_category = new_category

    session.flush()
    return actor


def favorAllInitActors(session: Session):
    """
    mark all actor in init category as liked if their folders are not deleted,
    delete his/her folder if you don't like hime/her before execute this
    :param session:
    :return:
    """
    actor_list = getActorsByCategory(session, ActorCategory.Init)
    for actor in actor_list:
        # check existence of actor's folder
        if os.path.exists(Configs.formatActorFolderPath(actor.actor_name)):
            actor.actor_category = ActorCategory.Liked


def repairRecords(session: Session):
    """
    refresh the records according to the existence of folders
    """
    stmt = select(ActorModel).where(ActorModel.actor_category != ActorCategory.Dislike)
    actor_list: ScalarResult[ActorModel] = session.scalars(stmt)
    for actor in actor_list:
        # deletion means you don't like
        if not os.path.exists(Configs.formatActorFolderPath(actor.actor_name)):
            if actor.actor_category == ActorCategory.Init:
                actor.actor_category = ActorCategory.Dislike
            else:
                actor.actor_category = ActorCategory.Enough
            PostCtrl.deleteAllPostOfActor(session, actor.actor_name)
