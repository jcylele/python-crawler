from sqlalchemy import ScalarResult, select, func, update
from sqlalchemy.orm import Session

from Ctrls import DbCtrl
from Models.ActorTagModel import ActorTagModel
from Models.ActorTagRelationship import ActorTagRelationship


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)


def getAllTagsUsedCount(session: Session) -> dict[int, int]:
    _query = session.query(
        ActorTagRelationship.tag_id,
        func.count(ActorTagRelationship.main_actor_id)
    ).group_by(ActorTagRelationship.tag_id)
    result = session.execute(_query).fetchall()
    count_map = {}
    for data in result:
        count_map[data[0]] = data[1]
    return count_map


def getTagUsedCount(session: Session, tag_id: int) -> int:
    # 使用select函数构建查询
    stmt = select(func.count()).select_from(ActorTagRelationship).where(
        ActorTagRelationship.tag_id == tag_id
    )
    # 执行查询并获取单一值结果
    count = session.execute(stmt).scalar_one()
    return count


def getActorTag(session: Session, tag_id: int) -> ActorTagModel:
    return session.get(ActorTagModel, tag_id)


def setTagName(session: Session, tag_id: int, tag_name: str):
    _query = update(ActorTagModel) \
        .where(ActorTagModel.tag_id == tag_id) \
        .values(tag_name=tag_name)
    session.execute(_query)


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
    session.delete(tag)
