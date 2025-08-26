from routers.schemas_others import TagCount
from sqlalchemy import BigInteger, func, select
from sqlalchemy.orm import Session, aliased

import Configs
from Consts import ResState
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Utils import LogUtil


def getTagRelative(session: Session, tag_id: int, limit: int) -> list[TagCount]:
    # 正确创建别名
    TagRel2 = aliased(ActorTagRelationship)

    stmt = (select(
        ActorTagRelationship.tag_id,
        func.count(ActorTagRelationship.main_actor_id)
    )
            .join(
        TagRel2,
        ActorTagRelationship.main_actor_id == TagRel2.main_actor_id
    )
            .where(TagRel2.tag_id == tag_id)
            .group_by(ActorTagRelationship.tag_id)
            .order_by(func.count(ActorTagRelationship.main_actor_id).desc())
            .limit(limit + 1))

    ret = session.execute(stmt).all()
    return [TagCount(tag_id=tag_id, count=count) for tag_id, count in ret]


def getScoresByTag(session: Session, tag_id: int) -> list[int]:
    """
    get scores of actors who have the tag
    """
    _query = select(ActorMainModel.score, func.count(ActorModel.actor_id)) \
        .join(ActorModel, ActorMainModel.main_actor_id == ActorModel.main_actor_id) \
        .join(ActorTagRelationship, ActorMainModel.main_actor_id == ActorTagRelationship.main_actor_id) \
        .where(ActorTagRelationship.tag_id == tag_id) \
        .group_by(ActorMainModel.score)
    ret = session.execute(_query).fetchall()

    scores = [0] * (Configs.MAX_SCORE + 1)
    for score, count in ret:
        scores[score] = count

    return scores


def getTagCountsByScore(session: Session, min_score: int, max_score: int, limit: int) -> list[TagCount]:
    """
    get tag counts used by actors who score between min_score and max_score
    """
    _query = (select(ActorTagRelationship.tag_id, func.count(ActorTagRelationship.main_actor_id))
              .join(ActorMainModel, ActorMainModel.main_actor_id == ActorTagRelationship.main_actor_id))
    if min_score > 0:
        _query = _query.where(ActorMainModel.score >= min_score)
    if 0 < max_score < Configs.MAX_SCORE:
        _query = _query.where(ActorMainModel.score <= max_score)
    _query = (_query.group_by(ActorTagRelationship.tag_id)
              .order_by(func.count(ActorTagRelationship.main_actor_id).desc())
              .limit(limit))
    ret = session.execute(_query).fetchall()
    return [TagCount(tag_id=tag_id, count=count) for tag_id, count in ret]


def getResSizeStats(session: Session) -> dict[int, int]:
    # 构建查询
    query = (
        select(
            ActorModel.actor_group_id,
            func.cast(func.sum(ResModel.res_size), BigInteger)
        )
        .join(PostModel, PostModel.actor_id == ActorModel.actor_id)
        .join(ResModel, ResModel.post_id == PostModel.post_id)
        .group_by(
            ActorModel.actor_group_id
        )
        .where(
            ResModel.res_state == ResState.Down
        )
    )

    # 执行查询
    result = session.execute(query).fetchall()

    # 处理结果
    size_map = {}
    for group_id, total_size in result:
        size_map[group_id] = total_size
        LogUtil.info(f"Group {group_id} total size: {total_size}")
    return size_map
