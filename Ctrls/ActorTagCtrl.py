from sqlalchemy import ScalarResult, select, func
from sqlalchemy.orm import Session

from Models.BaseModel import ActorTagModel, ActorTagRelationship


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)

def getActorCountWithTag(session: Session) -> int:
    session.query(
        func.count(ActorTagRelationship.actor_name).label('actor_count')
        , ActorTagRelationship.tag_id).group_by(ActorTagRelationship.tag_id)

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
