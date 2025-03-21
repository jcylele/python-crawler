from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

import Configs
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship


def getTagRelative(session: Session, tag_id: int, limit: int):
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
    return [{'tag_id': tag_id, 'count': count} for tag_id, count in ret]

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


def getTagCountsByScore(session: Session, min_score: int, max_score: int, limit: int):
    """
    get tag counts used by actors who score between min_score and max_score
    """
    _query = (session.query(ActorTagRelationship.tag_id, func.count(ActorTagRelationship.main_actor_id))
              .join(ActorMainModel, ActorMainModel.main_actor_id == ActorTagRelationship.main_actor_id))
    if min_score > 0:
        _query = _query.where(ActorMainModel.score >= min_score)
    if 0 < max_score < Configs.MAX_SCORE:
        _query = _query.where(ActorMainModel.score <= max_score)
    _query = (_query.group_by(ActorTagRelationship.tag_id)
              .order_by(func.count(ActorTagRelationship.main_actor_id).desc())
              .limit(limit))
    ret = session.execute(_query).fetchall()
    return [{'tag_id': tag_id, 'count': count} for tag_id, count in ret]
