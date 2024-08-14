from sqlalchemy import ScalarResult, select, func
from sqlalchemy.orm import Session

from Ctrls import DbCtrl
from Models.BaseModel import ActorTagModel, ActorTagRelationship


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)


def getAllTagsUsedCount(session: Session) -> dict[int, int]:
    _query = session.query(
        ActorTagRelationship.tag_id,
        func.count(ActorTagRelationship.actor_name)
    ).group_by(ActorTagRelationship.tag_id)
    result = session.execute(_query).fetchall()
    count_map = {}
    for data in result:
        count_map[data[0]] = data[1]
    return count_map


def getTagUsedCount(session: Session, tag_id: int) -> int:
    _query = session.query(ActorTagRelationship) \
        .where(ActorTagRelationship.tag_id == tag_id)
    return DbCtrl.queryCount(_query)


def getActorTag(session: Session, tag_id: int) -> ActorTagModel:
    return session.get(ActorTagModel, tag_id)


def addActorTag(session: Session, tag: ActorTagModel) -> ActorTagModel:
    session.add(tag)
    session.flush()
    return tag


def getMinPriority(session: Session, group: int) -> int:
    # func.min()
    max_priority = (group + 1) * 100 - 1
    min_priority = group * 100
    _query = session.query(func.min(ActorTagModel.tag_priority)) \
        .where(ActorTagModel.tag_priority >= min_priority) \
        .where(ActorTagModel.tag_priority <= max_priority)
    return session.execute(_query).scalar()


def deleteActorTag(session: Session, tag_id: int):
    tag = getActorTag(session, tag_id)
    if tag is None:
        return
    for rel in tag.rel_actors:
        session.delete(rel)
    session.delete(tag)
