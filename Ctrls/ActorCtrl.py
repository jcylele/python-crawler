# ActorModel related operations

import os
import shutil

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session, Query

import Configs
from Ctrls import PostCtrl, DbCtrl, ResCtrl
from Models.BaseModel import ActorModel, ActorCategory, ActorTagRelationship
from routers.web_data import ActorConditionForm


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

    createActorFolder(actor_name)

    actor = getActor(session, actor_name)
    if actor is not None:
        return actor

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


def _buildQuery(session: Session, form: ActorConditionForm) -> Query:
    _query = session.query(ActorModel)
    # name
    if form.name is not None and len(form.name) > 0:
        _query = _query.where(ActorModel.actor_name.like(f'%{form.name}%'))
    # category
    actor_category_list = form.get_category_list()
    _query = _query.where(ActorModel.actor_category.in_(actor_category_list))
    # tag
    if form.no_tag:
        _query = _query.where(~ActorModel.rel_tags.any())
    elif len(form.tag_list) > 0:
        _query = _query.where(ActorModel.rel_tags.any(ActorTagRelationship.tag_id.in_(form.tag_list)))

    return _query


def getActorCount(session: Session, form: ActorConditionForm) -> int:
    _query = _buildQuery(session, form)
    return DbCtrl.queryCount(_query)


def getActorList(session: Session, form: ActorConditionForm, limit: int = 0, start: int = 0) -> ScalarResult[
    ActorModel]:
    _query = _buildQuery(session, form)
    if start != 0:
        _query = _query.offset(start)
    if limit != 0:
        _query = _query.limit(limit)
    return session.scalars(_query)


def getActorsByCategory(session: Session, category: ActorCategory) -> ScalarResult[
    ActorModel]:
    """
    search actors by category
    """
    _query = (session.query(ActorModel)
              .order_by(ActorModel.actor_name)
              .where(ActorModel.actor_category == category))
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
        actor_folder = Configs.formatActorFolderPath(actor.actor_name)
        if os.path.exists(actor_folder):
            shutil.rmtree(actor_folder)
        PostCtrl.deleteAllFilesOfActor(session, actor.actor_name)
    # set field
    actor.actor_category = new_category

    session.flush()
    return actor


def changeActorStar(session: Session, actor_name: str, star: bool) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.star == star:
        return actor
    # set field
    actor.star = star
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
            PostCtrl.deleteAllFilesOfActor(session, actor.actor_name)
