# ActorModel related operations

import os
import re
import shutil

from sqlalchemy import ScalarResult, select
from sqlalchemy.orm import Session, Query

import Configs
from Ctrls import PostCtrl, DbCtrl, FileInfoCacheCtrl
from Models.ActorInfo import ActorInfo
from Models.BaseModel import ActorModel, ActorCategory, ActorTagRelationship, ResState
from Utils import LogUtil
from routers.web_data import ActorConditionForm


def getActorInfo(session: Session, actor_name: str) -> ActorInfo:
    actor = getActor(session, actor_name)
    if actor is None:
        LogUtil.error(f"get actorInfo failed, actor {actor_name} not exist")
        return None
    return ActorInfo(actor)


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


def addActor(session: Session, actor_info: ActorInfo) -> ActorModel:
    """
    create a record for the actor, skip if already exist
    :return: actor record
    """

    createActorFolder(actor_info.actor_name)

    actor = getActor(session, actor_info.actor_name)
    if actor is not None:
        return actor

    actor = ActorModel(actor_name=actor_info.actor_name,
                       actor_platform=actor_info.actor_platform,
                       actor_link=actor_info.actor_link)
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
    # score
    if form.min_score > 0:
        _query = _query.where(ActorModel.score >= form.min_score)
    if 0 < form.max_score < 10:
        _query = _query.where(ActorModel.score <= form.max_score)
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


def changeActorTags(session: Session, actor_name: str, tag_list: list[int]) -> ActorModel:
    actor = getActor(session, actor_name)

    tag_dict = {}
    remove_list = []

    for tag_id in tag_list:
        tag_dict[tag_id] = True

    for tag in actor.rel_tags:
        if tag.tag_id in tag_dict:
            tag_dict.pop(tag.tag_id)
        else:
            remove_list.append(tag.tag_id)

    for tag_id in remove_list:
        for rel in actor.rel_tags:
            if rel.tag_id == tag_id:
                actor.rel_tags.remove(rel)
                session.delete(rel)
                break

    for tag_id in tag_dict:
        relation = ActorTagRelationship()
        relation.tag_id = tag_id
        relation.actor_name = actor_name
        actor.rel_tags.append(relation)

    session.flush()
    return actor


__HasFiles = {
    ActorCategory.Init: True,
    ActorCategory.Liked: True,
    ActorCategory.Dislike: False,
    ActorCategory.Enough: False,
}


def removeDownloadingFiles(session: Session):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                matchObj = re.match(r'^(.+)_\d+_\d+\.\w+$', file)
                if matchObj:
                    actor_name = matchObj.group(1)
                    actor = getActor(session, actor_name)
                    if actor and not __HasFiles[actor.actor_category]:
                        LogUtil.info(f"remove downloading file {file}")
                        os.remove(os.path.join(root, file))
    except Exception as e:
        pass


def changeActorCategory(session: Session, actor_name: str, new_category: ActorCategory) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.actor_category == new_category:
        return actor
    oldHas = __HasFiles.get(actor.actor_category)
    newHas = __HasFiles.get(new_category)
    if oldHas != newHas:
        if oldHas:
            actor_folder = Configs.formatActorFolderPath(actor.actor_name)
            if os.path.exists(actor_folder):
                shutil.rmtree(actor_folder)
                FileInfoCacheCtrl.RemoveDownloadingFiles(actor.actor_name)

            PostCtrl.BatchSetResStates(session, actor.actor_name, ResState.Del)
        else:
            createActorFolder(actor.actor_name)
            PostCtrl.BatchSetResStates(session, actor.actor_name, ResState.Init)

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


def changeActorScore(session: Session, actor_name: str, score: int) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.score == score:
        return actor
    # set field
    actor.score = score
    session.flush()
    return actor


def changeActorRemark(session: Session, actor_name: str, remark: str) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.remark == remark:
        return actor
    # set field
    actor.remark = remark
    session.flush()
    return actor


def linkActors(session: Session, actor_names: [str]):
    # merge all tags
    all_tags = set()
    for actor_name in actor_names:
        actor = getActor(session, actor_name)
        for tag in actor.rel_tags:
            all_tags.add(tag.tag_id)
    # apply tags to all actors
    main_actor_name = actor_names[0]
    for actor_name in actor_names:
        actor = getActor(session, actor_name)
        actor.main_actor = main_actor_name
        new_tags = all_tags.copy()
        for tag in actor.rel_tags:
            new_tags.remove(tag.tag_id)
        for tag_id in new_tags:
            relation = ActorTagRelationship()
            relation.tag_id = tag_id
            relation.actor_name = actor_name
            actor.rel_tags.append(relation)
    # flush
    session.flush()
    # get updated actors
    actor_list = []
    for actor_name in actor_names:
        actor = getActor(session, actor_name)
        actor_list.append(actor)
    return actor_list


def getLinkedActors(session: Session, actor_name: str):
    actor = getActor(session, actor_name)
    if actor.main_actor is None:
        return [actor]

    stmt = (
        select(ActorModel)
            .where(ActorModel.main_actor == actor.main_actor)
    )
    actor_list: ScalarResult[ActorModel] = session.scalars(stmt)
    return [a for a in actor_list]
