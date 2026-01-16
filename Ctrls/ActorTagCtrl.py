from sqlalchemy import ScalarResult, delete, select, func, update
from sqlalchemy.orm import Session

from Consts import ErrorCode
from Models.ActorMainModel import ActorMainModel
from Models.ActorTagModel import ActorTagModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.Exceptions import BusinessException
from routers.web_data import TagUsedInfo


def getAllActorTags(session: Session) -> ScalarResult[ActorTagModel]:
    stmt = select(ActorTagModel).order_by(ActorTagModel.tag_priority)
    return session.scalars(stmt)


def getAllTagsUsedInfo(session: Session) -> dict[int, TagUsedInfo]:
    _query = (
        select(
            ActorTagRelationship.tag_id,
            func.count(ActorTagRelationship.main_actor_id),
            func.avg(ActorMainModel.score)
        )
        .select_from(ActorTagRelationship)
        .join(ActorMainModel, ActorMainModel.main_actor_id == ActorTagRelationship.main_actor_id)
        .group_by(ActorTagRelationship.tag_id)
    )
    result = session.execute(_query).fetchall()
    count_map: dict[int, TagUsedInfo] = {}
    for data in result:
        count_map[data[0]] = TagUsedInfo(
            used_count=data[1], avg_score=float(data[2]))
    return count_map  # type: ignore


def getTagUsedInfo(session: Session, tag_id: int) -> TagUsedInfo:
    # 使用select函数构建查询
    stmt = (
        select(
            func.count(ActorTagRelationship.main_actor_id),
            func.avg(ActorMainModel.score)
        )
        .select_from(ActorTagRelationship)
        .join(ActorMainModel, ActorMainModel.main_actor_id == ActorTagRelationship.main_actor_id)
        .where(
            ActorTagRelationship.tag_id == tag_id
        )
    )
    # 执行查询并获取单一值结果
    result = session.execute(stmt).fetchone()
    return TagUsedInfo(used_count=result[0], avg_score=float(result[1]))


def getActorTag(session: Session, tag_id: int) -> ActorTagModel:
    tag = session.get(ActorTagModel, tag_id)
    if tag is None:
        raise BusinessException(ErrorCode.TagNotFound)
    return tag


def setTagName(session: Session, tag_id: int, tag_name: str):
    _query = update(ActorTagModel) \
        .where(ActorTagModel.tag_id == tag_id) \
        .values(tag_name=tag_name)
    session.execute(_query)


def addActorTag(session: Session, tag: ActorTagModel) -> ActorTagModel:
    session.add(tag)
    session.flush()
    return tag


def deleteActorTag(session: Session, tag_id: int):
    _query = delete(ActorTagModel) \
        .where(ActorTagModel.tag_id == tag_id)
    session.execute(_query)
