# ActorModel related operations

import os
import re
import shutil
from typing import Union
from sqlalchemy import ScalarResult, select, delete, update
from sqlalchemy.orm import Session, Query

import Configs
from Consts import NoticeType, ActorLogType, GroupCondType
from Ctrls import PostCtrl, ResCtrl, DbCtrl, FileInfoCacheCtrl, ActorGroupCtrl, NoticeCtrl, ActorLogCtrl
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


def getActorByInfo(session: Session, actor_info: ActorInfo) -> ActorModel:
    _query = select(ActorModel) \
        .where(ActorModel.actor_name == actor_info.actor_name) \
        .where(ActorModel.actor_platform == actor_info.actor_platform)
    return session.scalar(_query)


def getActorsByName(session: Session, actor_name: str) -> list[ActorModel]:
    query = session.query(ActorModel).where(ActorModel.actor_name == actor_name)
    ret = session.execute(query).scalars()
    return list(ret)


def createActorFolder(actor: Union[ActorInfo, ActorModel]):
    os.makedirs(Configs.formatActorFolderPath(actor.actor_id, actor.actor_name), exist_ok=True)


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

    actor = ActorModel(actor_name=actor_info.actor_name,
                       actor_platform=actor_info.actor_platform,
                       actor_link=actor_info.actor_link,
                       actor_group_id=group_id)
    session.add(actor)
    session.flush()

    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Add)
    createActorFolder(actor)

    return actor


def _buildQuery(session: Session, form: ActorConditionForm) -> Query:
    _query = session.query(ActorModel.actor_id)
    # name   split by || when count > 1 exact match, else fuzzy
    if form.name is not None and len(form.name) > 0:
        name_list = form.name.split("||")
        if len(name_list) > 1:
            name_list = [x for x in name_list if x]
            _query = _query.where(ActorModel.actor_name.in_(name_list))
        else:
            _query = _query.where(ActorModel.actor_name.like(f'%{name_list[0]}%'))
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


def getAllActorCount(session: Session) -> int:
    _query = session.query(ActorModel)
    return DbCtrl.queryCount(_query)


def _sortQuery(_query: Query, form: ActorConditionForm) -> Query:
    sort_clauses = []
    for sort_item in form.sort_items:
        if sort_item.sort_type == SortType.Score:
            sort_clause = ActorModel.score
        elif sort_item.sort_type == SortType.TotalPostCount:
            sort_clause = ActorModel.total_post_count
        elif sort_item.sort_type == SortType.CategoryTime:
            sort_clause = ActorModel.group_time
        else:
            raise SystemError(f"invalid sort type {sort_item.sort_type}")

        if not sort_item.sort_asc:
            sort_clause = sort_clause.desc()

        sort_clauses.append(sort_clause)

    # default
    sort_clauses.append(ActorModel.actor_name)

    return _query.order_by(*sort_clauses)


def getActorList(session: Session, form: ActorConditionForm, limit: int = 0, start: int = 0) -> ScalarResult[int]:
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


def _innerSetActorTags(session: Session, actor_id: int, tag_list: Union[list[int], set[int]]):
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

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Tag, *tag_list)


def changeActorTags(session: Session, actor_id: int, tag_list: list[int]) -> list[ActorModel]:
    actor_ids = getLinkedActorIds(session, actor_id)
    # set field
    for aid in actor_ids:
        _innerSetActorTags(session, aid, tag_list)

    session.flush()
    return [getActor(session, aid) for aid in actor_ids]


def removeOutdatedFiles(session: Session):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                matchObj = re.match(r'^(.+)_(\d+)_(\d+)\.\w+$', file)
                if matchObj is None:
                    continue
                post_id = int(matchObj.group(2))
                res_index = int(matchObj.group(3))
                res = ResCtrl.getResByIndex(session, post_id, res_index)
                if res.res_state == ResState.Del:
                    LogUtil.info(f"remove downloading file {file}")
                    os.remove(os.path.join(root, file))
    except Exception as e:
        pass


def checkGroupCondition(session: Session, actor: ActorModel, group_id: int) -> tuple[bool, str]:
    cond_list = ActorGroupCtrl.getGroupConditions(session, group_id)
    for cond in cond_list:
        if cond.cond_type == GroupCondType.MinScore:
            if actor.score < cond.cond_param:
                return False, f"actor {actor.actor_name} score < {cond.cond_param / 2}"
        elif cond.cond_type == GroupCondType.MaxScore:
            if actor.score > cond.cond_param:
                return False, f"actor {actor.actor_name} score > {cond.cond_param / 2}"
        elif cond.cond_type == GroupCondType.HasAnyTag:
            tag_count = len(actor.rel_tags)
            if (cond.cond_param == 0) != (tag_count == 0):
                if tag_count == 0:
                    err_msg = f"actor {actor.actor_name} has no tag"
                else:
                    err_msg = f"actor {actor.actor_name} has {tag_count} tags"
                return False, err_msg
        elif cond.cond_type == GroupCondType.Linked:
            if (actor.main_actor_id == 0) != (cond.cond_param == 0):
                if actor.main_actor_id == 0:
                    err_msg = f"actor {actor.actor_name} is not linked"
                else:
                    err_msg = f"actor {actor.actor_name} is linked"
                return False, err_msg

    return True, ""


def changeActorGroup(session: Session, actor_id: int, new_group_id: int) -> tuple[bool, ActorModel, str]:
    actor = getActor(session, actor_id)
    # no change
    if actor.actor_group_id == new_group_id:
        return False, actor, f"actor {actor.actor_name} already in group {actor.actor_group.group_name}"
    # check group condition
    ok, err_msg = checkGroupCondition(session, actor, new_group_id)
    if not ok:
        return False, actor, err_msg

    oldHas = actor.actor_group.has_folder
    new_group = ActorGroupCtrl.getActorGroup(session, new_group_id)
    newHas = new_group.has_folder
    if oldHas != newHas:
        if oldHas:
            deleteAllRes(session, actor)
            last_post_id = PostCtrl.getMaxPostId(session, actor_id)
            actor.last_post_id = last_post_id
        else:
            createActorFolder(actor)

    # set field
    actor.setGroup(new_group_id)
    session.flush()

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Group, new_group_id)

    return True, actor, f"actor {actor.actor_name} join group {new_group.group_name}"


def ResetActorPosts(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    actor.last_post_id = 0

    PostCtrl.batchSetResStates(session, actor_id, ResState.Init)

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.ResetPost)


def deleteAllRes(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        FileInfoCacheCtrl.RemoveDownloadingFiles(actor.actor_name)

    PostCtrl.batchSetResStates(session, actor.actor_id, ResState.Del)


def clearActorFolder(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)
    if not os.path.exists(actor_folder):
        return
    # set res state according to file existence
    PostCtrl.removeCurrentResFiles(session, actor.actor_id)
    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.ClearFolder)
    # remove folder
    shutil.rmtree(actor_folder)
    # recreate folder
    createActorFolder(actor)


def _innerSetActorScore(session: Session, actor: ActorModel, score: int):
    if actor.score == score:
        return
    actor.score = score
    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Score, score)


def changeActorScore(session: Session, actor_id: int, score: int) -> list[ActorModel]:
    actors_ids = getLinkedActorIds(session, actor_id)
    actors = [getActor(session, aid) for aid in actors_ids]
    # set field
    for actor in actors:
        _innerSetActorScore(session, actor, score)

    session.flush()
    return actors


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


def unlinkActors(session: Session, actor_ids: list[int]) -> bool:
    if not checkDistinct(actor_ids):
        return False
    # check all actors belong to the same group, and all actors in the group are selected
    actor_list = [getActor(session, actor_id) for actor_id in actor_ids]
    main_actor_id = 0
    for actor in actor_list:
        if actor.main_actor_id == 0:
            return False
        if main_actor_id == 0:
            main_actor_id = actor.main_actor_id
        elif main_actor_id != actor.main_actor_id:
            return False

    stmt = session.query(ActorModel).where(ActorModel.main_actor_id == main_actor_id)
    actor_count = DbCtrl.queryCount(stmt)
    if actor_count > len(actor_ids):
        return False

    for actor_id in actor_ids:
        actor = getActor(session, actor_id)
        actor.main_actor_id = 0
        ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Unlink)

    return True


def linkActors(session: Session, actor_ids: list[int]) -> bool:
    if not checkDistinct(actor_ids):
        return False
    # check all actors belong to the same group or no group
    actor_list = [getActor(session, actor_id) for actor_id in actor_ids]
    main_actor_id = 0
    for actor in actor_list:
        if actor.main_actor_id != 0:
            if main_actor_id == 0:
                main_actor_id = actor.main_actor_id
            elif main_actor_id != actor.main_actor_id:
                return False

    if main_actor_id == 0:
        main_actor_id = actor_ids[0]

    max_score = 0
    all_tags = set()

    # calc max score and all tags
    actor_names = [actor.actor_name for actor in actor_list]
    for actor in actor_list:
        if actor.score > max_score:
            max_score = actor.score
        for tag in actor.rel_tags:
            all_tags.add(tag.tag_id)

    # apply link
    for actor in actor_list:
        actor.main_actor_id = main_actor_id
        ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Link, *actor_names)

        _innerSetActorScore(session, actor, max_score)
        _innerSetActorTags(session, actor.actor_id, all_tags)

    return True


def getLinkedActorGroups(session: Session, actor_id: int) -> list[int]:
    actor = getActor(session, actor_id)
    if actor.main_actor_id == 0:
        return [actor.actor_group_id]

    stmt = (
        select(ActorModel.actor_group_id)
        .where(ActorModel.main_actor_id == actor.main_actor_id)
        .order_by(ActorModel.actor_group_id)
    )
    group_ids = session.scalars(stmt)
    return [gid for gid in group_ids]


def getLinkedActorIds(session: Session, actor_id: int) -> list[int]:
    actor = getActor(session, actor_id)
    if actor.main_actor_id == 0:
        return [actor_id]

    stmt = (
        select(ActorModel.actor_id)
        .where(ActorModel.main_actor_id == actor.main_actor_id)
        .order_by(ActorModel.actor_group_id, ActorModel.actor_name)
    )
    actor_ids = session.scalars(stmt)
    return [aid for aid in actor_ids]


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


def checkDistinct(id_list: list[int]) -> bool:
    return len(set(id_list)) == len(id_list)


def isLinkChecked(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    return actor.link_checked


def setActorLinkChecked(session: Session, actor_id: int):
    stmt = (
        update(ActorModel)
        .where(ActorModel.actor_id == actor_id)
        .values(link_checked=True)
    )
    session.execute(stmt)


def checkActorLink(session, actor_infos: list[ActorInfo], init_group: int):
    actor_infos.sort(key=lambda x: x.actor_name)
    main_actor_ids = set()
    for actor_info in actor_infos:
        actor = getActorByInfo(session, actor_info)
        if actor is None:
            actor = addActor(session, actor_info, init_group)
        actor_info.actor_id = actor.actor_id
        main_actor_ids.add(actor.main_actor_id)

    if len(main_actor_ids) > 1 or 0 in main_actor_ids:
        actor_names = [actor_info.actor_name for actor_info in actor_infos]
        NoticeCtrl.addNoticeStrict(session, NoticeType.HasLinkedAccount, actor_names)
    else:
        names = ",".join([actor_info.actor_name for actor_info in actor_infos])
        LogUtil.info(f"actors linked: {names}")

    for actor_info in actor_infos:
        setActorLinkChecked(session, actor_info.actor_id)


_post_fix = ["vip", "free", "official"]
_pre_post_fix = [".", "-", "_"]


def findAllSimilarActors(session: Session):
    for postfix in _post_fix:
        _findSimilarOfPostfix(session, postfix)


def _findSimilarOfPostfix(session: Session, postfix: str):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.like(f'%{postfix}'))
    )
    actor_names = session.scalars(stmt)
    len_post_fix = len(postfix)
    for actor_name in actor_names:
        prepost = actor_name[-len_post_fix - 1]
        if prepost in _pre_post_fix:
            actor_name = actor_name[:-len_post_fix - 1]
        else:
            actor_name = actor_name[:-len_post_fix]
        _findSimilarOfName(session, actor_name)


def _findSimilarOfName(session: Session, pure_actor_name: str):
    possible_names = [pure_actor_name]
    for postfix in _post_fix:
        possible_names.append(pure_actor_name + postfix)
        for prepostfix in _pre_post_fix:
            possible_names.append(pure_actor_name + prepostfix + postfix)

    stmt = (
        select(ActorModel)
        .where(ActorModel.actor_name.in_(possible_names))
    )
    result = session.scalars(stmt)

    main_ids = set()
    actor_names = []
    for actor in result:
        main_ids.add(actor.main_actor_id)
        actor_names.append(actor.actor_name)

    if len(actor_names) > 1:
        if (len(main_ids) > 1) or (0 in main_ids):
            # not all actors are linked
            NoticeCtrl.addNoticeStrict(session, NoticeType.SimilarActorName, actor_names)
    elif len(actor_names) == 1:
        pass
    else:
        raise Exception(f"WTF, no actor found by pure name {pure_actor_name}")
