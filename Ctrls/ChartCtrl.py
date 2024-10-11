from sqlalchemy import func, select
from sqlalchemy.orm import Session

import Configs
from Models.BaseModel import ActorTagRelationship, ActorModel


def getTagRelative(session: Session, tag_id: int, limit: int):
    _query1 = select(ActorTagRelationship.actor_id) \
        .where(ActorTagRelationship.tag_id == tag_id)
    _query2 = select(ActorTagRelationship.tag_id, func.count(ActorTagRelationship.actor_id)) \
        .where(ActorTagRelationship.actor_id.in_(_query1)) \
        .group_by(ActorTagRelationship.tag_id) \
        .order_by(func.count(ActorTagRelationship.actor_id).desc()) \
        .limit(limit + 1)  # self is included
    ret = session.execute(_query2).fetchall()
    return [{'tag_id': tag_id, 'count': count} for tag_id, count in ret]


def getScoresByTag(session: Session, tag_id: int) -> list[int]:
    _query = session.query(ActorTagRelationship) \
        .where(ActorTagRelationship.tag_id == tag_id)
    rels = session.scalars(_query)
    scores = [0] * (Configs.MAX_SCORE + 1)
    for rel in rels:
        scores[rel.actor.score] += 1
    return scores


def getTagCountsByScore(session: Session, min_score: int, max_score: int, limit: int):
    """
    get tag counts used by actors who score between min_score and max_score
    """
    _query = (session.query(ActorTagRelationship.tag_id, func.count(ActorTagRelationship.actor_id))
              .join(ActorModel, ActorModel.actor_id == ActorTagRelationship.actor_id))
    if min_score > 0:
        _query = _query.where(ActorModel.score >= min_score)
    if 0 < max_score < Configs.MAX_SCORE:
        _query = _query.where(ActorModel.score <= max_score)
    _query = (_query.group_by(ActorTagRelationship.tag_id)
              .order_by(func.count(ActorTagRelationship.actor_id).desc())
              .limit(limit))
    ret = session.execute(_query).fetchall()
    return [{'tag_id': tag_id, 'count': count} for tag_id, count in ret]
