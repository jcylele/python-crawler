# ActorModel related operations

import os
import re
import shutil

from sqlalchemy import ScalarResult, select, delete
from sqlalchemy.orm import Session, Query

import Configs
from Consts import NoticeType, ActorLogType
from Ctrls import PostCtrl, DbCtrl, FileInfoCacheCtrl, ActorGroupCtrl, NoticeCtrl, ActorLogCtrl
from Models.ActorInfo import ActorInfo
from Models.BaseModel import ActorModel, ActorTagRelationship, ResState
from Utils import LogUtil
from routers.web_data import ActorConditionForm, SortType


def getActorInfo(session: Session, actor_id: int) -> ActorInfo:
    actor = getActor(session, actor_id)
    if actor is None:
        LogUtil.error(f"get actorInfo failed, actor {actor_id} not exist")
        return None
    return ActorInfo(actor)


def getActor(session: Session, actor_id: int) -> ActorModel:
    """
    get record of the actor
    :return:
    """
    return session.get(ActorModel, actor_id)


def getActorByName(session: Session, actor_name: str) -> ActorModel:
    """
    get record of the actor
    :return:
    """
    return session.query(ActorModel).where(ActorModel.actor_name == actor_name).first()


def createActorFolder(actor_name: str):
    """
    create a folder for the actor
    :param actor_name:
    :return:
    """
    os.makedirs(Configs.formatActorFolderPath(actor_name), exist_ok=True)


def checkSameActorName(session: Session, actor_name: str):
    _query = session.query(ActorModel) \
        .where(ActorModel.actor_name == actor_name)
    actor = session.execute(_query).fetchone()
    if actor is not None:
        NoticeCtrl.addNotice(session, NoticeType.SameActorName, actor_name)


def addActor(session: Session, actor_info: ActorInfo, group_id: int) -> ActorModel:
    """
    create a record for the actor, skip if already exist
    :return: actor record
    """
    checkSameActorName(session, actor_info.actor_name)
    createActorFolder(actor_info.actor_name)

    actor = ActorModel(actor_name=actor_info.actor_name,
                       actor_platform=actor_info.actor_platform,
                       actor_link=actor_info.actor_link,
                       actor_group_id=group_id)
    session.add(actor)
    session.flush()

    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Add)

    return actor


def hasActor(session: Session, actor_info: ActorInfo) -> bool:
    _query = session.query(ActorModel) \
        .where(ActorModel.actor_name == actor_info.actor_name) \
        .where(ActorModel.actor_platform == actor_info.actor_platform)
    actor = session.execute(_query).fetchone()
    return actor is not None


def _buildQuery(session: Session, form: ActorConditionForm) -> Query:
    _query = session.query(ActorModel)
    # name
    if form.name is not None and len(form.name) > 0:
        _query = _query.where(ActorModel.actor_name.like(f'%{form.name}%'))
    # has link
    if form.linked:
        _query = _query.where(ActorModel.main_actor_id != 0)
    # category
    if len(form.group_id_list) > 0:
        _query = _query.where(ActorModel.actor_group_id.in_(form.group_id_list))
    # tag
    if form.no_tag:
        _query = _query.where(~ActorModel.rel_tags.any())
    elif len(form.tag_list) > 0:
        _query = _query.where(ActorModel.rel_tags.any(ActorTagRelationship.tag_id.in_(form.tag_list)))
    # score
    if form.min_score > 0:
        _query = _query.where(ActorModel.score >= form.min_score)
    if 0 < form.max_score < Configs.MAX_SCORE:
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
    # default sort
    if form.sort_type == SortType.Default:
        return _query.order_by(ActorModel.actor_name)

    mainClause = None
    if form.sort_type == SortType.Score:
        mainClause = ActorModel.score
    elif form.sort_type == SortType.TotalPostCount:
        mainClause = ActorModel.total_post_count
    elif form.sort_type == SortType.CategoryTime:
        mainClause = ActorModel.group_time
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


def getActorsByGroup(session: Session, group_id: int) -> ScalarResult[ActorModel]:
    """
    search actors by category
    """
    _query = (session.query(ActorModel)
              .where(ActorModel.actor_group_id == group_id))
    return session.scalars(_query)


def changeActorTags(session: Session, actor_id: int, tag_list: list[int]) -> ActorModel:
    # delete all old tags
    _query = delete(ActorTagRelationship) \
        .where(ActorTagRelationship.actor_id == actor_id)
    session.execute(_query)

    # add new tags
    for tag_id in tag_list:
        relation = ActorTagRelationship()
        relation.tag_id = tag_id
        relation.actor_id = actor_id
        session.add(relation)

    session.flush()

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Tag, *tag_list)

    # return updated actor
    actor = getActor(session, actor_id)
    return actor


def removeOutdatedFiles(session: Session):
    # cache folder status
    folder_dict = {}
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                matchObj = re.match(r'^(.+)_\d+_\d+\.\w+$', file)
                if matchObj is None:
                    continue
                actor_name = matchObj.group(1)
                # get and cache folder status
                if actor_name not in folder_dict:
                    actor = getActorByName(session, actor_name)
                    if actor is not None:
                        folder_dict[actor_name] = actor.actor_group.has_folder
                # remove file if actor not exist or has no folder
                if actor_name not in folder_dict or not folder_dict[actor_name]:
                    LogUtil.info(f"remove downloading file {file}")
                    os.remove(os.path.join(root, file))
    except Exception as e:
        pass


def changeActorGroup(session: Session, actor_id: int, new_group_id: int) -> ActorModel:
    actor = getActor(session, actor_id)
    # no change
    if actor.actor_group_id == new_group_id:
        return actor
    oldHas = actor.actor_group.has_folder
    new_group = ActorGroupCtrl.getActorGroup(session, new_group_id)
    newHas = new_group.has_folder
    if oldHas != newHas:
        if oldHas:
            deleteAllRes(session, actor)
            last_post_id = PostCtrl.getMaxPostId(session, actor_id)
            actor.last_post_id = last_post_id
        else:
            createActorFolder(actor.actor_name)

    # set field
    actor.setGroup(new_group_id)
    session.flush()

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Group, new_group_id)

    return actor


def ResetActorPosts(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    actor.last_post_id = 0

    PostCtrl.batchSetResStates(session, actor_id, ResState.Init)

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.ResetPost)


def deleteAllRes(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(actor.actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        FileInfoCacheCtrl.RemoveDownloadingFiles(actor.actor_name)

    PostCtrl.batchSetResStates(session, actor.actor_id, ResState.Del)


def clearActorFolder(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(actor.actor_name)
    if not os.path.exists(actor_folder):
        return
    # set res state according to file existence
    PostCtrl.removeCurrentResFiles(session, actor.actor_id)
    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.ClearFolder)
    # remove folder
    shutil.rmtree(actor_folder)
    # recreate folder
    createActorFolder(actor.actor_name)


def changeActorScore(session: Session, actor_id: int, score: int) -> ActorModel:
    actor = getActor(session, actor_id)
    # no change
    if actor.score == score:
        return actor
    # set field
    actor.score = score
    session.flush()

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Score, score)

    return actor


def changeActorRemark(session: Session, actor_id: int, remark: str) -> ActorModel:
    actor = getActor(session, actor_id)
    # no change
    if actor.remark == remark:
        return actor
    # set field
    actor.remark = remark
    session.flush()

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Remark, remark)

    return actor


def unlinkActors(session: Session, actor_ids: [str]):
    actor_list = []
    for actor_id in actor_ids:
        actor = getActor(session, actor_id)
        actor.main_actor_id = 0
        actor_list.append(actor)
        ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Unlink)
    return actor_list


def linkActors(session: Session, actor_ids: [str]):
    max_score = 0
    # merge all tags
    all_tags = set()
    actor_names = []
    for actor_id in actor_ids:
        actor = getActor(session, actor_id)
        actor_names.append(actor.actor_name)
        if actor.score > max_score:
            max_score = actor.score
        for tag in actor.rel_tags:
            all_tags.add(tag.tag_id)
    # apply tags to all actors
    main_actor_id = actor_ids[0]
    for actor_id in actor_ids:
        actor = getActor(session, actor_id)
        actor.score = max_score
        actor.main_actor_id = main_actor_id
        new_tags = all_tags.copy()
        for tag in actor.rel_tags:
            new_tags.remove(tag.tag_id)
        for tag_id in new_tags:
            relation = ActorTagRelationship()
            relation.tag_id = tag_id
            relation.actor_id = actor_id
            actor.rel_tags.append(relation)
    # flush
    session.flush()
    # get updated actors
    actor_list = []
    for actor_id in actor_ids:
        actor = getActor(session, actor_id)
        actor_list.append(actor)

        ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Link, *actor_names)
        ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Score, max_score)
        ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Tag, *all_tags)
    return actor_list


def getLinkedActors(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    if actor.main_actor_id == 0:
        return [actor]

    stmt = (
        select(ActorModel)
        .where(ActorModel.main_actor_id == actor.main_actor_id)
    )
    actor_list: ScalarResult[ActorModel] = session.scalars(stmt)
    return [a for a in actor_list]


def getActorFileInfo(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    actor_file_info = FileInfoCacheCtrl.GetCachedFileSizes(actor_id)
    if actor_file_info is None:
        actor_file_info = actor.calc_res_file_info()
        FileInfoCacheCtrl.CacheFileSizes(actor_id, actor_file_info)

    return {
        'res_info': actor_file_info,
        'total_post_count': actor.total_post_count,
        'unfinished_post_count': PostCtrl.getPostCount(session, actor_id, False),
        'finished_post_count': PostCtrl.getPostCount(session, actor_id, True)
    }
