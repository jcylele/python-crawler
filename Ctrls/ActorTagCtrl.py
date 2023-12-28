from sqlalchemy import ScalarResult, select, func
from sqlalchemy.orm import Session

from Models.BaseModel import ActorTagModel, ActorTagRelationship


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)


def getTagUsedCount(session: Session) -> dict[int, int]:
    _query = session.query(
        ActorTagRelationship.tag_id,
        func.count(ActorTagRelationship.actor_name)
    ).group_by(ActorTagRelationship.tag_id)
    result = session.execute(_query).fetchall()
    count_map = {}
    for data in result:
        count_map[data[0]] = data[1]
    return count_map


def getActorTag(session: Session, tag_id: int) -> ActorTagModel:
    return session.get(ActorTagModel, tag_id)


def addActorTag(session: Session, tag: ActorTagModel) -> ActorTagModel:
    session.add(tag)
    session.flush()
    return tag


def deleteActorTag(session: Session, tag_id: int):
    tag = getActorTag(session, tag_id)
    if tag is None:
        return
    for rel in tag.rel_actors:
        session.delete(rel)
    session.delete(tag)
