from sqlalchemy import ScalarResult, select
from sqlalchemy.orm import Session

from Ctrls import DbCtrl
from Models.BaseModel import ActorGroupModel, ActorModel
from routers.web_data import ActorGroupForm


def getAllActorGroups(session: Session) -> ScalarResult[ActorGroupModel]:
    stmt = select(ActorGroupModel).order_by(ActorGroupModel.group_priority)
    return session.scalars(stmt)


def getActorGroup(session: Session, group_id: int) -> ActorGroupModel:
    return session.get(ActorGroupModel, group_id)


def addNewActorGroup(session: Session, form: ActorGroupForm) -> ActorGroupModel:
    group = ActorGroupModel()
    group.group_name = form.group_name
    group.group_desc = form.group_desc
    group.group_color = form.group_color
    group.group_priority = form.group_priority
    group.has_folder = form.has_folder
    session.add(group)
    session.flush()
    return group


def updateActorGroup(session: Session, group: ActorGroupForm):
    real_group: ActorGroupModel = session.get(ActorGroupModel, group.group_id)
    real_group.group_name = group.group_name
    real_group.group_desc = group.group_desc
    real_group.group_priority = group.group_priority
    real_group.group_color = group.group_color
    real_group.has_folder = group.has_folder
    session.flush()
    return real_group


def deleteActorGroup(session: Session, group_id: int) -> bool:
    _query = session.query(ActorModel) \
        .where(ActorModel.actor_category == group_id)
    actor_count = DbCtrl.queryCount(_query)
    if actor_count > 0:
        return False
    group = session.get(ActorGroupModel, group_id)
    if group is None:
        return True
    session.delete(group)
    return True
