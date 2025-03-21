from sqlalchemy import ScalarResult, func, select, delete
from sqlalchemy.orm import Session

from Consts import GroupCondType
from Ctrls import DbCtrl
from Models.ActorGroupCondModel import ActorGroupCondModel
from Models.ActorGroupModel import ActorGroupModel
from Models.ActorModel import ActorModel
from routers.web_data import ActorGroupForm, ActorGroupCond


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
    # 使用Query API直接计数
    actor_count = session.query(func.count(ActorModel.actor_id)).filter(
        ActorModel.actor_group_id == group_id
    ).scalar()

    if actor_count > 0:
        return False

    # 删除演员组
    session.execute(
        delete(ActorGroupModel).where(ActorGroupModel.group_id == group_id)
    )

    return True


def setGroupCondition(session: Session, group_id: int, cond_list: list[ActorGroupCond]):
    _query = delete(ActorGroupCondModel) \
        .where(ActorGroupCondModel.group_id == group_id)
    session.execute(_query)

    for cond in cond_list:
        cond_model = ActorGroupCondModel(group_id=group_id,
                                         cond_type=GroupCondType(
                                             cond.cond_type),
                                         cond_param=cond.cond_param)
        session.add(cond_model)
    session.flush()


def getGroupConditions(session: Session, group_id: int):
    return session.query(ActorGroupCondModel).where(ActorGroupCondModel.group_id == group_id).all()
