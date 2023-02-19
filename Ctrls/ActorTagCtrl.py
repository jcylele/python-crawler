from sqlalchemy import ScalarResult, select
from sqlalchemy.orm import Session

from Models.BaseModel import ActorTagModel


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)


def getActorTag(session: Session, tag_id: int) -> ActorTagModel:
    return session.get(ActorTagModel, tag_id)


def addActorTag(session: Session, tag: ActorTagModel) -> ActorTagModel:
    session.add(tag)
    session.flush()
    return tag


def deleteActorTag(session: Session, tag_id: int):
    actor_tag_model = getActorTag(session, tag_id)
    for rel in actor_tag_model.rel_actors:
        session.delete(rel)
    session.delete(actor_tag_model)
    return actor_tag_model.tag_name

