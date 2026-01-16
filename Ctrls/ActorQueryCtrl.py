
from sqlalchemy import and_, or_, asc, desc, exists, func, select, Select, case
from sqlalchemy.orm import Session, aliased

import Configs
from Consts import EFixFilter, ResState, SortType, BoolEnum
from Ctrls import ActorFileCtrl
from Models.PostModel import PostModel
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel, actor_all_post_completed
from Models.ActorTagRelationship import ActorTagRelationship
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorFavoriteRelationship import ActorFavoriteRelationship
from Utils import PyUtil
from routers.schemas_others import CommentCount
from routers.web_data import ActorConditionForm, LinkFilter, TagFilter

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


def _filterLinkQuery(query: Select, form: LinkFilter) -> Select:
    if form.linked == BoolEnum.ALL:
        return query
    if form.linked == BoolEnum.FALSE:
        query = query.where(ActorModel.main_actor_id == ActorModel.actor_id)
        return query

    # linked
    query = query.where(ActorModel.main_actor_id != ActorModel.actor_id)

    # 使用 GROUP BY 聚合查询，一次扫描解决数量和条件判断
    stmt = select(ActorModel.main_actor_id).where(
        ActorModel.main_actor_id.is_not(None)
    ).group_by(ActorModel.main_actor_id)

    having_clauses = []

    # 1. 数量筛选 (Count)
    if form.min_link_count > 0:
        count_expr = func.count(ActorModel.actor_id)
        having_clauses.append(count_expr >= form.min_link_count)

    # 2. 分组逻辑筛选 (Group Logic)
    if form.contain_group_id > 0:
        cond = func.max(
            case((ActorModel.actor_group_id == form.contain_group_id, 1), else_=0)
        ) == 1
        having_clauses.append(cond)

    # 如果有筛选条件，则应用 HAVING 并通过 IN 子查询过滤主查询
    if having_clauses:
        stmt = stmt.having(and_(*having_clauses))
        query = query.where(ActorMainModel.main_actor_id.in_(stmt))

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

    if form.group_id_list:
        query = query.where(ActorModel.actor_group_id.in_(form.group_id_list))

    if form.folder_id != 0:
        folder_id_abs = abs(form.folder_id)  # 取绝对值
        exists_condition = exists().where(
            and_(
                ActorFavoriteRelationship.actor_id == ActorModel.actor_id,
                ActorFavoriteRelationship.folder_id == folder_id_abs
            )
        )
        if form.folder_id < 0:
            query = query.where(~exists_condition)
        else:
            query = query.where(exists_condition)

    # tag filter
    query = _filterTagQuery(query, form.tag_filter)

    # link filter
    query = _filterLinkQuery(query, form.link_filter)

    if form.min_score > 0:
        query = query.where(ActorMainModel.score >= form.min_score)
    if form.max_score < Configs.MAX_SCORE:
        query = query.where(ActorMainModel.score <= form.max_score)

    # remark filter, fuzzy match
    if form.has_remark == BoolEnum.TRUE:
        query = query.where(ActorMainModel.has_remark == True)
        remark = PyUtil.stripToNone(form.remark_str)
        if remark:
            query = query.where(ActorMainModel.remark.like(f"%{remark}%"))
    elif form.has_remark == BoolEnum.FALSE:
        query = query.where(ActorMainModel.has_remark == False)
    else:
        pass

    # comment filter, exact match
    if form.has_comment == BoolEnum.TRUE:
        query = query.where(ActorModel.has_comment == True)
        comment = PyUtil.stripToNone(form.comment_str)
        if comment:
            query = query.where(ActorModel.comment == comment)
    elif form.has_comment == BoolEnum.FALSE:
        query = query.where(ActorModel.has_comment == False)
    else:
        pass
    # progess, including post and res
    if form.post_completed == BoolEnum.TRUE:
        query = query.where(actor_all_post_completed(True))
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
        query = query.where(actor_all_post_completed(False))
    else:
        pass

    # post count filter
    if form.fix_filter & EFixFilter.Overflow:
        query = query.where(ActorModel.current_post_count >
                            ActorModel.total_post_count)
    if form.fix_filter & EFixFilter.TotalZero:
        query = query.where(ActorModel.total_post_count == 0)
    if form.fix_filter & EFixFilter.LinkNotChecked:
        query = query.where(ActorModel.link_checked == False)
    if form.fix_filter & EFixFilter.IconNotExists:
        query = query.where(ActorModel.icon_hash.is_(None))
    if form.fix_filter & EFixFilter.MissingPosts:
        query = query.where(ActorModel.has_missing_posts == True)

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


def getActorCountInFolders(session: Session) -> dict[int, int]:
    stmt = (select(ActorFavoriteRelationship.folder_id,
                   func.count(ActorFavoriteRelationship.actor_id)).group_by(ActorFavoriteRelationship.folder_id))
    count_map: dict[int, int] = {}
    for row in session.execute(stmt):
        count_map[row[0]] = row[1]
    return count_map


def _sortQuery(_query: Select, form: ActorConditionForm) -> Select:
    for sort_item in form.sort_items:
        order_func = sort_item.sort_asc and asc or desc
        if sort_item.sort_type == SortType.Score:
            _query = _query.order_by(order_func(ActorMainModel.score))
        elif sort_item.sort_type == SortType.FavoriteCount:
            _query = _query.order_by(order_func(ActorModel.favorite_count))
        elif sort_item.sort_type == SortType.TotalPostCount:
            _query = _query.order_by(order_func(ActorModel.total_post_count))
        elif sort_item.sort_type == SortType.CompletedPostCount:
            _query = _query.order_by(order_func(
                ActorModel.completed_post_count))
        elif sort_item.sort_type == SortType.CategoryTime:
            _query = _query.order_by(order_func(ActorModel.group_time))
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
    if form.post_completed == BoolEnum.TRUE and form.res_completed != BoolEnum.ALL:
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


def getActorsWithoutTotalPostCount(session: Session) -> list[int]:
    _query = (select(ActorModel.actor_id)
              .where(ActorModel.total_post_count == 0)
              .where(ActorModel.manual_done == False))
    return list(session.scalars(_query))
