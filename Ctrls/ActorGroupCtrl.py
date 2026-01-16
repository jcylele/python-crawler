from sqlalchemy import ScalarResult, select, delete, exists
from sqlalchemy.orm import Session

from Consts import ErrorCode, GroupCondType
from Models.ActorGroupCondModel import ActorGroupCondModel
from Models.ActorGroupModel import ActorGroupModel
from Models.ActorModel import ActorModel
from Models.Exceptions import BusinessException
from routers.web_data import ActorGroupForm, ActorGroupCond


def getAllActorGroups(session: Session) -> list[ActorGroupModel]:
    stmt = select(ActorGroupModel).order_by(ActorGroupModel.group_priority)
    return list(session.scalars(stmt))


def getActorGroup(session: Session, group_id: int) -> ActorGroupModel:
    return session.get(ActorGroupModel, group_id)


def __assign_form_to_group(group: ActorGroupModel, form: ActorGroupForm):
    group.group_name = form.name
    group.group_desc = form.desc
    group.group_priority = form.priority
    group.group_color = form.group_color
    group.flags = form.flags


def addNewActorGroup(session: Session, form: ActorGroupForm) -> ActorGroupModel:
    group = ActorGroupModel()
    __assign_form_to_group(group, form)
    session.add(group)
    session.flush()
    return group


def updateActorGroup(session: Session, group_id: int, form: ActorGroupForm):
    real_group: ActorGroupModel = session.get(ActorGroupModel, group_id)
    __assign_form_to_group(real_group, form)
    session.flush()
    return real_group


def deleteActorGroup(session: Session, group_id: int):
    # check if there are actors in the group
    exists_query = select(exists().where(
        ActorModel.actor_group_id == group_id
    ))
    actor_exists = session.scalar(exists_query)
    if actor_exists:
        raise BusinessException(ErrorCode.GroupHasActors)

    # delete the group
    session.execute(
        delete(ActorGroupModel).where(ActorGroupModel.group_id == group_id)
    )


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
    stmt = select(ActorGroupCondModel).where(
        ActorGroupCondModel.group_id == group_id)
    return session.scalars(stmt)


def checkGroupCondition(session: Session, actor: ActorModel, group_id: int) -> int:
    main_actor = actor.main_actor
    cond_list = getGroupConditions(session, group_id)
    for cond in cond_list:
        if cond.cond_type == GroupCondType.MinScore:
            if main_actor.score < cond.cond_param:
                return cond.cond_id
        elif cond.cond_type == GroupCondType.MaxScore:
            if main_actor.score > cond.cond_param:
                return cond.cond_id
        elif cond.cond_type == GroupCondType.HasAnyTag:
            tag_count = len(main_actor.rel_tags)
            if (cond.cond_param == 0) != (tag_count == 0):
                return cond.cond_id
        elif cond.cond_type == GroupCondType.Linked:
            if (actor.is_linked) != (cond.cond_param == 1):
                return cond.cond_id
        elif cond.cond_type == GroupCondType.HasRemark:
            if (main_actor.has_remark) != (cond.cond_param == 1):
                return cond.cond_id

    return 0
