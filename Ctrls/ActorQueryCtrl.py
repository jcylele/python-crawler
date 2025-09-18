
from sqlalchemy import and_, or_, asc, desc, exists, func, select, Select
from sqlalchemy.orm import Session, aliased

import Configs
from Consts import ResState, SortType, BoolEnum
from Ctrls import ActorFileCtrl
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorFavoriteRelationship import ActorFavoriteRelationship
from routers.schemas_others import CommentCount
from routers.web_data import ActorConditionForm, TagFilter

_sort_file_size_map: dict[SortType, list[ResState]] = {
    SortType.InitFileSize: [ResState.Init],
    SortType.DownFileSize: [ResState.Down],
    SortType.TotalFileSize: [ResState.Init, ResState.Down],
}


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
        name_list = [name for name in form.name.split("||")]
        real_name_list = [name.strip() for name in name_list if name.strip()]
        if len(name_list) > 1:  # || found, need to be accurate
            query = query.where(ActorModel.actor_name.in_(real_name_list))
        elif real_name_list:  # no || found, need to be fuzzy, skip empty name
            query = query.where(
                ActorModel.actor_name.like(f"%{real_name_list[0]}%"))

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

    if form.post_completed == BoolEnum.TRUE:
        query = query.where(and_(
            ActorModel.last_post_fetch_time is not None,
            ActorModel.completed_post_count == ActorModel.total_post_count
        ))
        if form.res_completed != BoolEnum.ALL:
            subquery = select(ActorFileInfoModel.actor_id).where(
                and_(
                    ActorFileInfoModel.actor_id == ActorModel.actor_id,
                    ActorFileInfoModel.res_state == ResState.Init,
                    ActorFileInfoModel.video_count > 0
                )
            ).exists()
            if form.res_completed == BoolEnum.TRUE:
                query = query.where(~subquery)
            else:
                query = query.where(subquery)
    elif form.post_completed == BoolEnum.FALSE:
        query = query.where(or_(
            ActorModel.last_post_fetch_time is None,
            ActorModel.completed_post_count != ActorModel.total_post_count
        ))
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


def getActorCountInGroups(session: Session) -> dict[int, int]:
    # 直接用select()和func.count()计数，最简洁高效
    stmt = select(ActorModel.actor_group_id, func.count(
        ActorModel.actor_id)).group_by(ActorModel.actor_group_id)
    count_map: dict[int, int] = {}
    for row in session.execute(stmt):
        count_map[row[0]] = row[1]
    return count_map


def _sortQuery(_query: Select, form: ActorConditionForm) -> Select:
    for sort_item in form.sort_items:
        order_func = sort_item.sort_asc and asc or desc
        if sort_item.sort_type == SortType.Score:
            _query = _query.order_by(order_func(ActorMainModel.score))
        elif sort_item.sort_type == SortType.TotalPostCount:
            _query = _query.order_by(order_func(ActorModel.total_post_count))
        elif sort_item.sort_type == SortType.CurPostCount:
            _query = _query.order_by(order_func(ActorModel.current_post_count))
        elif sort_item.sort_type == SortType.CategoryTime:
            _query = _query.order_by(order_func(ActorModel.group_time))
        elif sort_item.sort_type == SortType.LastPostFetchTime:
            _query = _query.order_by(
                order_func(ActorModel.last_post_fetch_time.is_(None)),
                order_func(ActorModel.last_post_fetch_time)
            )
        elif sort_item.sort_type == SortType.LastResDownloadTime:
            _query = _query.order_by(
                order_func(ActorModel.last_res_download_time.is_not(None)),
                order_func(ActorModel.last_res_download_time)
            )
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


def _unsortedActorList(session: Session, form: ActorConditionForm) -> list[int]:
    _query = _filterQuery(_initQuery(False), form)
    return list(session.scalars(_query))


def _needFileInfo(form: ActorConditionForm) -> bool:
    if form.post_completed and form.res_completed:
        return True
    if any(
        sort_item.sort_type in _sort_file_size_map
        for sort_item in form.sort_items
    ):
        return True
    return False


def getActorList(session: Session, form: ActorConditionForm, limit: int = 0, start: int = 0) -> list[int]:
    if _needFileInfo(form):
        actor_ids = _unsortedActorList(session, form)
        ActorFileCtrl.ensureBatchActorFileInfo(session, actor_ids)

    _query = _sortQuery(_filterQuery(_initQuery(False), form), form)
    if start != 0:
        _query = _query.offset(start)
    if limit != 0:
        _query = _query.limit(limit)
    return list(session.scalars(_query))


def getActorsByGroup(session: Session, group_id: int) -> list[ActorModel]:
    """
    search actors by category
    """
    _query = (select(ActorModel)
              .where(ActorModel.actor_group_id == group_id))
    return session.scalars(_query)


def getComments(session: Session) -> list[CommentCount]:
    _query = (select(ActorModel.comment, func.count(ActorModel.actor_id))
              .where(ActorModel.has_comment == True)
              .group_by(ActorModel.comment)
              .order_by(func.count(ActorModel.actor_id).desc(), ActorModel.comment))
    return [CommentCount(comment=row[0], count=row[1]) for row in session.execute(_query)]
