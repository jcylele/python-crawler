# ActorModel related operations
import itertools
import os
import re
import shutil
from typing import Union, List, Dict, Tuple, Set

from sqlalchemy import ScalarResult, and_, exists, func, select, delete, update, Select
from sqlalchemy.orm import Session, aliased

import Configs
from Consts import NoticeType, ActorLogType, GroupCondType, ResState, ResType
from Ctrls import PostCtrl, ResCtrl, ActorGroupCtrl, NoticeCtrl, ActorLogCtrl, ActorFileCtrl
from Models.ActorFavoriteRelationship import ActorFavoriteRelationship
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorInfo import ActorInfo
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.FavoriteFolderModel import FavoriteFolderModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Utils import LogUtil, PyUtil
from routers.web_data import ActorConditionForm, SortType, LinkActorForm, TagFilter, BoolEnum, ActorVideoInfo

_sort_file_size_map: Dict[SortType, List[ResState]] = {
    SortType.DownFileSize: [ResState.Down],
    SortType.CurFileSize: [ResState.Init, ResState.Down, ResState.Skip],
    SortType.TotalFileSize: [],
}


# region single actor


def getActorInfo(session: Session, actor_id: int) -> ActorInfo:
    actor = getActor(session, actor_id)
    if actor is None:
        LogUtil.error(f"get actorInfo failed, actor {actor_id} not exist")
        return None
    return ActorInfo(actor)


def getActor(session: Session, actor_id: int) -> ActorModel:
    return session.get(ActorModel, actor_id)

def getActors(session: Session, actor_ids: list[int]) -> list[ActorModel]:
    return list(session.scalars(select(ActorModel).where(ActorModel.actor_id.in_(actor_ids))))

def getMainActor(session: Session, main_actor_id: int) -> ActorMainModel:
    return session.get(ActorMainModel, main_actor_id)


def getActorByInfo(session: Session, actor_info: ActorInfo) -> ActorModel:
    _query = select(ActorModel) \
        .where(ActorModel.actor_name == actor_info.actor_name) \
        .where(ActorModel.actor_platform == actor_info.actor_platform)
    return session.scalar(_query)


def getActorsByName(session: Session, actor_name: str) -> list[ActorModel]:
    query = select(ActorModel).where(
        ActorModel.actor_name == actor_name)
    return list(session.scalars(query))


def createActorFolder(actor: Union[ActorInfo, ActorModel]):
    os.makedirs(Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name), exist_ok=True)


def checkSameActorName(session: Session, actor_name: str):
    exists_query = select(exists().where(
        ActorModel.actor_name == actor_name
    ))
    name_exists = session.scalar(exists_query)
    if name_exists:
        NoticeCtrl.addNotice(session, NoticeType.SameActorName, actor_name)


def addActor(session: Session, actor_info: ActorInfo, group_id: int) -> ActorModel:
    checkSameActorName(session, actor_info.actor_name)

    actor = ActorModel(actor_name=actor_info.actor_name,
                       actor_platform=actor_info.actor_platform,
                       actor_link=actor_info.actor_link,
                       actor_group_id=group_id)
    session.add(actor)
    session.flush()  # ensure actor_id is set

    # add main_actor
    main_actor = ActorMainModel(
        main_actor_id=actor.actor_id
    )
    session.add(main_actor)
    # set main_actor_id to self
    actor.main_actor_id = actor.actor_id
    session.flush()

    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Add)
    createActorFolder(actor)

    return actor


def getActorFileInfo(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    return {
        'res_info': ActorFileCtrl.getActorFileInfo(session, actor_id),
        'total_post_count': actor.total_post_count,
        'unfinished_post_count': PostCtrl.getPostCount(session, actor_id, False),
        'finished_post_count': PostCtrl.getPostCount(session, actor_id, True)
    }


def __removeDeletedFile(session: Session, file_path: str, post_id: int, res_index: int):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res.res_state == ResState.Del:
        LogUtil.info(f"remove downloading file {file_path}")
        os.remove(file_path)


def removeOutdatedFiles(session: Session):
    ActorFileCtrl.traverseDownloadingFiles(session, __removeDeletedFile)


def deleteAllRes(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    if os.path.exists(actor_folder):
        shutil.rmtree(actor_folder)
        ActorFileCtrl.RemoveDownloadingFiles(session, actor)

    PostCtrl.batchSetResStates(session, actor.actor_id, ResState.Del)


def clearActorFolder(session: Session, actor: ActorModel):
    actor_folder = Configs.formatActorFolderPath(
        actor.actor_id, actor.actor_name)
    if not os.path.exists(actor_folder):
        return
    # set res state according to file existence
    PostCtrl.removeCurrentResFiles(session, actor.actor_id)
    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.ClearFolder)
    # remove folder
    shutil.rmtree(actor_folder)
    # recreate folder
    createActorFolder(actor)


def getActorVideoStats(session: Session, actor_id: int) -> list[ActorVideoInfo]:
    landscape_info = ActorVideoInfo(True)
    portrait_info = ActorVideoInfo(False)
    stmt = select(
        ResModel
    ).join(
        PostModel, PostModel.post_id == ResModel.post_id
    ).where(
        PostModel.actor_id == actor_id,
        ResModel.res_state == ResState.Down,
        ResModel.res_type == ResType.Video
    )

    ret = session.scalars(stmt)
    for res in ret:
        if res.res_width >= res.res_height:
            landscape_info.add_info(res.res_duration, res.res_size)
        else:
            portrait_info.add_info(res.res_duration, res.res_size)
    return [landscape_info, portrait_info]


# endregion

# region query


def _initQuery(is_count: bool = False) -> Select:
    if is_count:
        query = select(func.count(ActorModel.actor_id))
    else:
        query = select(ActorModel.actor_id)
    return query.join(
        ActorMainModel,
        onclause=ActorModel.main_actor_id == ActorMainModel.main_actor_id
    )


def _filterTagQuery(query: Select, form: TagFilter) -> Select:
    if form.no_tag:
        query = query.where(~ActorMainModel.rel_tags.any())
    else:
        # 必须包含的tag (AND)
        if form.must_have:
            for tag_id in form.must_have:
                tag_alias = aliased(ActorTagRelationship)
                query = query.join(
                    tag_alias,
                    onclause=and_(
                        ActorMainModel.main_actor_id == tag_alias.main_actor_id,
                        tag_alias.tag_id == tag_id
                    )
                )

        # 每组至少包含一个的tag (OR)
        for tag_group in form.any_of:
            if not tag_group:
                continue
            tag_alias = aliased(ActorTagRelationship)
            query = query.outerjoin(
                tag_alias,
                onclause=and_(
                    ActorMainModel.main_actor_id == tag_alias.main_actor_id,
                    tag_alias.tag_id.in_(tag_group)
                )
            ).where(tag_alias.main_actor_id.is_not(None))  # 确保至少匹配一个

        # 不能包含的tag (NOT)
        if form.must_not_have:
            tag_alias = aliased(ActorTagRelationship)
            query = query.outerjoin(
                tag_alias,
                onclause=and_(
                    ActorMainModel.main_actor_id == tag_alias.main_actor_id,
                    tag_alias.tag_id.in_(form.must_not_have)
                )
            ).where(tag_alias.main_actor_id.is_(None))  # 确保不匹配任何

    return query


def _filterQuery(query: Select, form: ActorConditionForm) -> Select:
    form.name = form.name.strip()
    if form.name:
        name_list = [name.strip()
                     for name in form.name.split("||") if name.strip()]
        if len(name_list) > 1:
            query = query.where(ActorModel.actor_name.in_(name_list))
        elif name_list:
            query = query.where(
                ActorModel.actor_name.like(f"%{name_list[0]}%"))

    if form.linked:
        query = query.where(ActorModel.main_actor_id != ActorModel.actor_id)

    if form.group_id_list:
        query = query.where(ActorModel.actor_group_id.in_(form.group_id_list))

    if form.folder_id:
        query = query.where(
            exists().where(
                and_(
                    ActorFavoriteRelationship.actor_id == ActorModel.actor_id,
                    ActorFavoriteRelationship.folder_id == form.folder_id
                )
            )
        )

    # tag filter
    query = _filterTagQuery(query, form.tag_filter)

    if form.min_score > 0:
        query = query.where(ActorMainModel.score >= form.min_score)
    if form.max_score < Configs.MAX_SCORE:
        query = query.where(ActorMainModel.score <= form.max_score)

    if form.has_remark == BoolEnum.TRUE:
        query = query.where(ActorMainModel.has_remark == True)
        remark = form.remark_str.strip()
        if remark:
            query = query.where(ActorMainModel.remark.like(f"%{remark}%"))
    elif form.has_remark == BoolEnum.FALSE:
        query = query.where(ActorMainModel.has_remark == False)
    else:
        pass

    return query


def getActorCount(session: Session, form: ActorConditionForm) -> int:
    _query = _initQuery(True)
    _query = _filterQuery(_query, form)
    return session.scalar(_query)


def getAllActorCount(session: Session) -> int:
    # 直接用select()和func.count()计数，最简洁高效
    stmt = select(func.count()).select_from(ActorModel)
    return session.scalar(stmt)


def getActorCountOfGroups(session: Session) -> list[tuple[int, int]]:
    # 直接用select()和func.count()计数，最简洁高效
    stmt = select(ActorModel.actor_group_id, func.count(
        ActorModel.actor_id)).group_by(ActorModel.actor_group_id)
    return [(row[0], row[1]) for row in session.execute(stmt)]


def _sortQuery(_query: Select, form: ActorConditionForm) -> Select:
    for sort_item in form.sort_items:
        if sort_item.sort_type == SortType.Score:
            sort_clause = ActorMainModel.score
            if not sort_item.sort_asc:
                sort_clause = sort_clause.desc()
            _query = _query.order_by(sort_clause)

        elif sort_item.sort_type == SortType.TotalPostCount:
            sort_clause = ActorModel.total_post_count
            if not sort_item.sort_asc:
                sort_clause = sort_clause.desc()
            _query = _query.order_by(sort_clause)

        elif sort_item.sort_type == SortType.CurPostCount:
            subq = select(func.count(PostModel.post_id)).where(
                PostModel.actor_id == ActorModel.actor_id
            ).scalar_subquery()

            if not sort_item.sort_asc:
                subq = subq.desc()
            _query = _query.order_by(subq)

        elif sort_item.sort_type == SortType.CategoryTime:
            sort_clause = ActorModel.group_time
            if not sort_item.sort_asc:
                sort_clause = sort_clause.desc()
            _query = _query.order_by(sort_clause)

        elif sort_item.sort_type in _sort_file_size_map:
            res_state_list = _sort_file_size_map[sort_item.sort_type]
            subq = (
                select(func.sum(ActorFileInfoModel.video_size))
                .where(ActorFileInfoModel.actor_id == ActorModel.actor_id)
            )
            state_count = len(res_state_list)
            if state_count > 1:
                subq = subq.where(
                    ActorFileInfoModel.res_state.in_(res_state_list)
                )
            elif state_count == 1:
                subq = subq.where(
                    ActorFileInfoModel.res_state == res_state_list[0]
                )
            subq = subq.scalar_subquery()
            if not sort_item.sort_asc:
                subq = subq.desc()
            _query = _query.order_by(subq)
    # default
    _query = _query.order_by(ActorModel.actor_name)

    return _query


def getUnsortedActorList(session: Session, form: ActorConditionForm) -> list[int]:
    _query = _filterQuery(_initQuery(False), form)
    return list(session.scalars(_query))


def getActorList(session: Session, form: ActorConditionForm, limit: int = 0, start: int = 0) -> list[int]:
    need_file_info = any(
        sort_item.sort_type in _sort_file_size_map
        for sort_item in form.sort_items
    )
    if need_file_info:
        actor_ids = getUnsortedActorList(session, form)
        ActorFileCtrl.ensureBatchActorFileInfo(session, actor_ids)

    _query = _sortQuery(_filterQuery(_initQuery(False), form), form)
    if start != 0:
        _query = _query.offset(start)
    if limit != 0:
        _query = _query.limit(limit)
    return list(session.scalars(_query))


def getActorsByGroup(session: Session, group_id: int) -> ScalarResult[ActorModel]:
    """
    search actors by category
    """
    _query = (select(ActorModel)
              .where(ActorModel.actor_group_id == group_id))
    return session.scalars(_query)


def isAllVideoDownloaded(session: Session, actor_id: int) -> bool:
    actor = getActor(session, actor_id)
    if actor.total_post_count == 0:
        return False
    completed_post_count = PostCtrl.getPostCount(session, actor_id, True)
    if completed_post_count < actor.total_post_count:
        return False
    file_info_list = ActorFileCtrl.getActorFileInfo(session, actor_id)
    for file_info in file_info_list:
        if (file_info.res_state == ResState.Init or file_info.res_state == ResState.Skip) and \
                file_info.video_count > 0:
            return False
    return True


def getFinishedActorList(session: Session, form: ActorConditionForm) -> list[int]:
    _query = _filterQuery(_initQuery(False), form)
    id_list = list(session.scalars(_query))
    return [id for id in id_list if isAllVideoDownloaded(session, id)]


# endregion

# region update actor / main_actor


def _innerSetActorTags(session: Session, main_actor_id: int, tag_list: Union[list[int], set[int]]):
    # delete all old tags
    _query = delete(ActorTagRelationship) \
        .where(ActorTagRelationship.main_actor_id == main_actor_id)
    session.execute(_query)

    # add new tags
    for tag_id in tag_list:
        rel_tag = ActorTagRelationship(
            tag_id=tag_id,
            main_actor_id=main_actor_id
        )
        session.add(rel_tag)


def changeActorTags(session: Session, actor_id: int, tag_list: list[int]) -> list[ActorModel]:
    # set tags for main_actor
    actor = getActor(session, actor_id)
    _innerSetActorTags(session, actor.main_actor_id, tag_list)

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Tag, *tag_list)

    session.flush()
    return linked_actors


def changeActorScore(session: Session, actor_id: int, score: int) -> list[ActorModel]:
    # change score for main_actor
    actor = getActor(session, actor_id)
    main_actor = actor.main_actor
    if main_actor.score == score:
        return []  # no change
    # set field
    main_actor.score = score

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Score, score)

    session.flush()
    return linked_actors


def changeActorComment(session: Session, actor_id: int, comment: str) -> ActorModel:
    # change comment for main_actor
    actor = getActor(session, actor_id)
    actor.comment = comment
    session.flush()
    return actor


def changeActorRemark(session: Session, actor_id: int, remark: str) -> list[ActorModel]:
    # process remark
    real_remark = PyUtil.stripToNone(remark)
    # change remark for main_actor
    actor = getActor(session, actor_id)
    main_actor: ActorMainModel = actor.main_actor

    if main_actor.remark == real_remark:
        return []  # no change

    # set field
    main_actor.remark = real_remark

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Remark, remark)

    session.flush()
    return linked_actors

def _setResStateToDowned(session: Session, file_path: str, post_id: int, res_index: int):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    res.res_state = ResState.Down

def ResetActorPosts(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    actor.last_post_id = 0

    PostCtrl.batchSetResStates(session, actor_id, ResState.Init)
    # set res state to downed if downloaded files exist
    ActorFileCtrl.traverseDownloadedFilesOfActor(session, actor, _setResStateToDowned)

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.ResetPost)


def _checkGroupCondition(session: Session, actor: ActorModel, group_id: int) -> tuple[bool, str]:
    main_actor = actor.main_actor
    cond_list = ActorGroupCtrl.getGroupConditions(session, group_id)
    for cond in cond_list:
        if cond.cond_type == GroupCondType.MinScore:
            if main_actor.score < cond.cond_param:
                return False, f"actor {actor.actor_name} score < {cond.cond_param / 2}"
        elif cond.cond_type == GroupCondType.MaxScore:
            if main_actor.score > cond.cond_param:
                return False, f"actor {actor.actor_name} score > {cond.cond_param / 2}"
        elif cond.cond_type == GroupCondType.HasAnyTag:
            tag_count = len(main_actor.rel_tags)
            if (cond.cond_param == 0) != (tag_count == 0):
                if tag_count == 0:
                    err_msg = f"actor {actor.actor_name} has no tag"
                else:
                    err_msg = f"actor {actor.actor_name} has {tag_count} tags"
                return False, err_msg
        elif cond.cond_type == GroupCondType.Linked:
            if (actor.isLinked()) != (cond.cond_param == 1):
                if actor.isLinked():
                    err_msg = f"actor {actor.actor_name} is linked"
                else:
                    err_msg = f"actor {actor.actor_name} is not linked"
                return False, err_msg

    return True, ""


def changeActorGroup(session: Session, actor_id: int, new_group_id: int) -> tuple[bool, ActorModel, str]:
    actor = getActor(session, actor_id)
    # no change
    if actor.actor_group_id == new_group_id:
        return False, actor, f"actor {actor.actor_name} already in group {actor.actor_group.group_name}"
    # check group condition
    ok, err_msg = _checkGroupCondition(session, actor, new_group_id)
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

    ActorLogCtrl.addActorLog(
        session, actor_id, ActorLogType.Group, new_group_id)

    return True, actor, f"actor {actor.actor_name} join group {new_group.group_name}"


# endregion

# region link related


def unlinkActors(session: Session, actor_ids: list[int]) -> tuple[bool, str]:
    actor_ids = distinct(actor_ids)
    # check all actors belong to the same group, and all actors in the group are selected
    actor_list = [getActor(session, actor_id) for actor_id in actor_ids]
    main_actor_id = 0
    for actor in actor_list:
        if not actor.isLinked():  # not linked
            return False
        if main_actor_id == 0:
            main_actor_id = actor.main_actor_id
        elif main_actor_id != actor.main_actor_id:  # not in same link
            return False, f"actors are in different links"

    # check if all actors included
    stmt = select(func.count(ActorModel.actor_id)).where(
        ActorModel.main_actor_id == main_actor_id)
    linked_actor_count = session.scalar(stmt)
    if linked_actor_count > len(actor_ids):
        return False, f"not all actors in the link are selected"

    main_actor = getMainActor(session, main_actor_id)
    if main_actor is None:
        LogUtil.error(f"main actor {main_actor_id} not found")
        return False, f"main actor {main_actor_id} not found"

    for actor in actor_list:
        # copy main_actor
        new_main_actor = ActorMainModel(
            main_actor_id=actor.actor_id,
            remark=main_actor.remark,
            score=main_actor.score
        )

        rel_tags = []
        # copy rel_tags
        for rel_tag in main_actor.rel_tags:
            new_rel_tag = ActorTagRelationship(
                tag_id=rel_tag.tag_id,
                main_actor_id=actor.actor_id
            )
            rel_tags.append(new_rel_tag)

        new_main_actor.rel_tags = rel_tags
        session.add(new_main_actor)

        # set main_actor_id to self
        actor.main_actor_id = actor.actor_id
        # add log
        ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Unlink)

    # delete main_actor, rel_tags will be deleted by cascade
    session.delete(main_actor)

    session.flush()
    return True, f"actors unlinked"


def linkActors(session: Session, form: LinkActorForm) -> tuple[bool, str]:
    actor_ids = distinct(form.actor_ids)
    # check all actors belong to the same link group or no group
    actor_list = [getActor(session, actor_id) for actor_id in actor_ids]
    # will be removed at the end
    old_main_actor_ids = set()
    old_main_actor_id = 0
    linked_actor_count = 0
    for actor in actor_list:
        old_main_actor_ids.add(actor.main_actor_id)
        if actor.isLinked():
            linked_actor_count += 1
            if old_main_actor_id == 0:
                old_main_actor_id = actor.main_actor_id
            elif old_main_actor_id != actor.main_actor_id:  # not in same link
                return False, f"actors are in different links"

    # check all linked actors are included
    if old_main_actor_id != 0:
        stmt = select(func.count(ActorModel.actor_id)).where(
            ActorModel.main_actor_id == old_main_actor_id)
        total_linked_actor_count = session.scalar(stmt)
        if total_linked_actor_count > linked_actor_count:
            return False, f"not all actors in the link are selected"

    # choose a new main_actor_id from actor_ids, exclude old_main_actor_id
    for actor_id in actor_ids:
        new_main_actor_id = -actor_id
        if new_main_actor_id != old_main_actor_id:
            break
    # create a new main_actor
    new_main_actor = ActorMainModel(
        main_actor_id=new_main_actor_id,
        remark=form.remark,
        score=form.score
    )

    rel_tags = []
    for tag_id in form.tag_list:
        rel_tag = ActorTagRelationship(
            tag_id=tag_id,
            main_actor_id=new_main_actor_id
        )
        rel_tags.append(rel_tag)
    # add new_main_actor along with rel_tags
    new_main_actor.rel_tags = rel_tags
    session.add(new_main_actor)

    actor_names = [actor.actor_name for actor in actor_list]
    # apply link
    for actor in actor_list:
        actor.main_actor_id = new_main_actor_id
        ActorLogCtrl.addActorLog(
            session, actor.actor_id, ActorLogType.Link, *actor_names)
        if form.score != 0:
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Score, form.score)
        if form.remark != "":
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Remark, form.remark)
        if len(form.tag_list) > 0:
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Tag, *form.tag_list)

    # flush to ensure old_main_actor_ids are not ref by actors now
    session.flush()

    # remove old main_actors along with rel_tags
    for main_actor_id in old_main_actor_ids:
        main_actor = session.get(ActorMainModel, main_actor_id)
        if main_actor:
            session.delete(main_actor)

    return True, f"actors linked: {', '.join(actor_names)}"


def getLinkedActorGroups(session: Session, actor_id: int) -> list[int]:
    actor = getActor(session, actor_id)
    if not actor.isLinked():
        return [actor.actor_group_id]

    stmt = (
        select(ActorModel.actor_group_id)
        .where(ActorModel.main_actor_id == actor.main_actor_id)
        .order_by(ActorModel.actor_group_id)
    )
    return list(session.scalars(stmt))


def getLinkedActors(session: Session, main_actor_id: int) -> list[ActorModel]:
    stmt = (
        select(ActorModel)
        .where(ActorModel.main_actor_id == main_actor_id)
        .order_by(ActorModel.actor_group_id, ActorModel.actor_name)
    )
    return list(session.scalars(stmt))


def getLinkedActorIds(session: Session, main_actor_id: int) -> list[int]:
    stmt = (
        select(ActorModel.actor_id)
        .where(ActorModel.main_actor_id == main_actor_id)
        .order_by(ActorModel.actor_group_id, ActorModel.actor_name)
    )
    return list(session.scalars(stmt))


def distinct(id_list: list[int]) -> list[int]:
    return list(set(id_list))


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
        NoticeCtrl.addNoticeStrict(
            session, NoticeType.HasLinkedAccount, actor_names)
    else:
        names = ",".join([actor_info.actor_name for actor_info in actor_infos])
        LogUtil.info(f"actors linked: {names}")

    for actor_info in actor_infos:
        setActorLinkChecked(session, actor_info.actor_id)


# endregion

# region find similar names


_pre_fix = ['the', 'free', 'goddess', 'only']
_post_fix = ["vip", "free", "official", "premium", "ppv", "clips"]
sp_chars = [".", "-", "_"]


def findAllSimilarActors(session: Session):
    for prefix in _pre_fix:
        _findSimilarByPrefix(session, prefix)

    for postfix in _post_fix:
        _findSimilarByPostfix(session, postfix)

    for sp_char in sp_chars:
        _findSimilarBySpChar(session, sp_char)

    _findSimilarByLastDigits(session)
    _findSimilarByLastXs(session)
    _findSimilarByLastChar(session)
    _find_similar_actor_names(session)


def _findSimilarByLastChar(session: Session):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.regexp_match('(.)\\1{2,}$'))
    )
    actor_names = session.scalars(stmt)
    for actor_name in actor_names:
        pure_actor_name = actor_name[:-1]
        possible_names = possibleNames(pure_actor_name)
        possible_names.append(actor_name)
        _checkAllPossibleNames(session, possible_names)


def _findSimilarBySpChar(session: Session, sp_char: str):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.regexp_match(f'\w+{sp_char}\w+'))
    )
    result1 = session.scalars(stmt)
    for actor_name in result1:
        possible_names = [actor_name]
        # split by mid, skip empty
        name_segments = [x for x in actor_name.split(sp_char) if x]
        # all permutations means all possible names
        perm = itertools.permutations(name_segments)
        for p in perm:
            possible_names.append("".join(p))
            for sp_char2 in sp_chars:
                possible_names.append(sp_char2.join(p))

        _checkAllPossibleNames(session, possible_names)


def _findSimilarByPrefix(session: Session, prefix: str):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.regexp_match(f'^{prefix}\w+'))
    )
    actor_names = session.scalars(stmt)
    for actor_name in actor_names:
        pure_actor_name = actor_name[len(prefix):]

        possible_names = possibleNames(pure_actor_name)
        _checkAllPossibleNames(session, possible_names)


def _findSimilarByPostfix(session: Session, postfix: str):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.regexp_match(f'\w+{postfix}$'))
    )
    actor_names = session.scalars(stmt)
    len_post_fix = len(postfix)
    for actor_name in actor_names:
        sp_char = actor_name[-len_post_fix - 1]
        if sp_char in sp_chars:
            pure_actor_name = actor_name[:-len_post_fix - 1]
        else:
            pure_actor_name = actor_name[:-len_post_fix]

        possible_names = possibleNames(pure_actor_name)
        _checkAllPossibleNames(session, possible_names)


def _findSimilarByLastDigits(session: Session):
    _findSimilarByEndChars(session, r'\d+$', lambda x: x.isdigit())


def _findSimilarByLastXs(session: Session):
    _findSimilarByEndChars(session, r'x+$', lambda x: x == "x")


def _findSimilarByEndChars(session: Session, str_reg: str, char_filter: callable):
    stmt = (
        select(ActorModel.actor_name)
        .where(ActorModel.actor_name.regexp_match(str_reg))
    )
    actor_names = session.scalars(stmt)
    for actor_name in actor_names:
        # trim right 0-9 chars
        index = len(actor_name) - 1
        while char_filter(actor_name[index]):
            index -= 1
        if index == -1:
            continue
        pure_actor_name = actor_name[:index + 1]

        possible_names = possibleNames(pure_actor_name)
        possible_names.append(actor_name)
        _checkAllPossibleNames(session, possible_names)


def possibleNames(pure_name: str):
    possible_names = [pure_name]
    for postfix in _post_fix:
        possible_names.append(pure_name + postfix)
        for sp_char in sp_chars:
            possible_names.append(pure_name + sp_char + postfix)

    # prefix and sp_char don't match
    for pre_fix in _pre_fix:
        possible_names.append(pre_fix + pure_name)

    return possible_names


def _checkAllPossibleNames(session: Session, possible_names: list[str]):
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
            NoticeCtrl.addNoticeStrict(
                session, NoticeType.SimilarActorName, actor_names)
    elif len(actor_names) == 1:
        pass
    else:
        raise Exception(f"WTF, no actor found for {possible_names}")


def _find_common_substrings(strings: List[str], length: int) -> Dict[int, Tuple[str, Set[str]]]:
    """
    使用固定长度的滚动哈希查找公共子串

    Args:
        strings: 输入字符串列表
        length: 固定的子串长度

    """
    # 存储所有子串哈希值及其出现的字符串
    hash_groups: Dict[int, Tuple[str, Set[str]]] = {}

    # 对每个字符串生成固定长度的子串哈希
    for s in strings:
        if len(s) < length:
            continue

        # 计算第一个子串的哈希值
        hash_value = 0
        for i in range(length):
            hash_value = (hash_value * 31 + ord(s[i])) & 0xFFFFFFFF

        # 存储第一个子串
        if hash_value not in hash_groups:
            hash_groups[hash_value] = (s[:length], set())
        hash_groups[hash_value][1].add(s)

        # 使用滚动哈希计算后续子串
        for i in range(1, len(s) - length + 1):
            # 减去最左边字符的贡献
            hash_value = (
                hash_value - (ord(s[i - 1]) * pow(31, length - 1, 0xFFFFFFFF))) & 0xFFFFFFFF
            # 乘以31并加上新字符
            hash_value = (hash_value * 31 +
                          ord(s[i + length - 1])) & 0xFFFFFFFF
            if hash_value not in hash_groups:
                hash_groups[hash_value] = (s[i:i + length], set())
            hash_groups[hash_value][1].add(s)

    return hash_groups


def _find_similar_actor_names(session: Session):
    stmt = (select(ActorModel.actor_name.distinct()))
    actor_names = session.scalars(stmt).fetchall()
    unique_sets = set()
    for length in range(30, 10, -1):
        name_group_dict = _find_common_substrings(actor_names, length)
        for name_tup in name_group_dict.values():
            if len(name_tup[1]) == 1:
                continue
            else:
                name_list = sorted(name_tup[1])
                tup = tuple(name_list)
                if tup not in unique_sets:
                    unique_sets.add(tup)
                    _checkAllPossibleNames(session, name_list)

# endregion
