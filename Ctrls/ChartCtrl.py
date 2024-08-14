from sqlalchemy.orm import Session

from Models.BaseModel import ActorTagRelationship, ActorModel


def getScoresByTag(session: Session, tag_id: int) -> list[int]:
    _query = session.query(ActorTagRelationship) \
        .where(ActorTagRelationship.tag_id == tag_id)
    rels = session.scalars(_query)
    scores = [0] * 11
    for rel in rels:
        scores[rel.actor.score] += 1
    return scores


def getTagsByScore(session: Session, min_score: int, max_score: int):
    _query = session.query(ActorModel)
    if min_score > 0:
        _query = _query.where(ActorModel.score >= min_score)
    if 0 < max_score < 10:
        _query = _query.where(ActorModel.score <= max_score)
    actors = session.scalars(_query)

    tag_map = {}
    for actor in actors:
        for rel_tag in actor.rel_tags:
            tag_id = rel_tag.tag_id
            if tag_id in tag_map:
                tag_map[tag_id] += 1
            else:
                tag_map[tag_id] = 1
    tag_list = [{'tag_id': tag_id, 'count': count} for tag_id, count in tag_map.items()]
    tag_list.sort(key=lambda x: x['count'])
    return tag_list
