# ActorModel related operations

import os
import re
import shutil

from sqlalchemy import ScalarResult, select
from sqlalchemy.orm import Session, Query

import Configs
from Ctrls import PostCtrl, DbCtrl, FileInfoCacheCtrl, ActorGroupCtrl
from Models.ActorInfo import ActorInfo
from Models.BaseModel import ActorModel, ActorTagRelationship, ResState
from Utils import LogUtil
from routers.web_data import ActorConditionForm, SortType


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


def addActor(session: Session, actor_info: ActorInfo, category: int) -> ActorModel:
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
                       actor_link=actor_info.actor_link,
                       actor_category=category)
    session.add(actor)
    session.flush()

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
    if len(form.category_list) > 0:
        _query = _query.where(ActorModel.actor_category.in_(form.category_list))
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
    # remark
    if form.remark_str is not None and len(form.remark_str) > 0:
        _query = _query.where(ActorModel.remark.like(f'%{form.remark_str}%'))
    elif form.remark_any:
        _query = _query.where(ActorModel.remark != "")
    return _query


def getActorCount(session: Session, form: ActorConditionForm) -> int:
    _query = _buildQuery(session, form)
    return DbCtrl.queryCount(_query)


def _sortQuery(_query: Query, form: ActorConditionForm) -> Query:
    # order_by(ActorModel.score.desc(), User.date_created.desc())
    if form.sort_type == SortType.Default:
        return _query

    mainClause = None
    if form.sort_type == SortType.Score:
        mainClause = ActorModel.score
    elif form.sort_type == SortType.TotalPostCount:
        mainClause = ActorModel.total_post_count
    elif form.sort_type == SortType.CategoryTime:
        mainClause = ActorModel.category_time
    else:
        raise SystemError(f"invalid sort type {form.sort_type}")

    if not form.sort_asc:
        mainClause = mainClause.desc()
    return _query.order_by(mainClause, ActorModel.actor_name)


def getActorList(session: Session, form: ActorConditionForm, limit: int = 0, start: int = 0) -> ScalarResult[
    ActorModel]:
    _query = _buildQuery(session, form)
    _query = _sortQuery(_query, form)
    if start != 0:
        _query = _query.offset(start)
    if limit != 0:
        _query = _query.limit(limit)
    return session.scalars(_query)


def getActorsByCategory(session: Session, category: int) -> ScalarResult[
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


def removeOutdatedFiles(session: Session):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                matchObj = re.match(r'^(.+)_\d+_\d+\.\w+$', file)
                if matchObj:
                    actor_name = matchObj.group(1)
                    actor = getActor(session, actor_name)
                    if actor and not actor.actor_group.has_folder:
                        LogUtil.info(f"remove downloading file {file}")
                        os.remove(os.path.join(root, file))
    except Exception as e:
        pass


def changeActorCategory(session: Session, actor_name: str, new_category: int) -> ActorModel:
    actor = getActor(session, actor_name)
    # no change
    if actor.actor_category == new_category:
        return actor
    oldHas = actor.actor_group.has_folder
    new_group = ActorGroupCtrl.getActorGroup(session, new_category)
    newHas = new_group.has_folder
    if oldHas != newHas:
        if oldHas:
            deleteAllRes(session, actor_name)
            last_post_id = PostCtrl.getMaxPostId(session, actor_name)
            actor.last_post_id = last_post_id
        else:
            createActorFolder(actor.actor_name)

    # set field
    actor.setCategory(new_category)
    session.flush()
    return actor


def ResetActorPosts(session: Session, actor_name: str):
    actor = getActor(session, actor_name)
    actor.last_post_id = 0

    PostCtrl.batchSetResStates(session, actor_name, ResState.Init)


def deleteAllRes(session: Session, actor_name: str):
    actor_folder = Configs.formatActorFolderPath(actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        FileInfoCacheCtrl.RemoveDownloadingFiles(actor_name)

    PostCtrl.batchSetResStates(session, actor_name, ResState.Del)


def clearActorFolder(session: Session, actor_name: str):
    actor_folder = Configs.formatActorFolderPath(actor_name)
    if not os.path.exists(actor_folder):
        return
    # remove cache first, prevent update to cache
    FileInfoCacheCtrl.RemoveCachedFileSizes(actor_name)
    # set res state according to file existence
    PostCtrl.removeCurrentResFiles(session, actor_name)
    # remove files
    shutil.rmtree(actor_folder)
    createActorFolder(actor_name)


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


def getActorFileInfo(session: Session, actor_name: str):
    actor = getActor(session, actor_name)
    actor_file_info = FileInfoCacheCtrl.GetCachedFileSizes(actor_name)
    if actor_file_info is None:
        actor_file_info = actor.calc_res_file_info()
        FileInfoCacheCtrl.CacheFileSizes(actor_name, actor_file_info)

    return {
        'res_info': actor_file_info,
        'total_post_count': actor.total_post_count,
        'unfinished_post_count': PostCtrl.getPostCount(session, actor_name, False),
        'finished_post_count': PostCtrl.getPostCount(session, actor_name, True)
    }
