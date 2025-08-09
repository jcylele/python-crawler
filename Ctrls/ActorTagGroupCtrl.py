from sqlalchemy import ScalarResult, select, delete
from sqlalchemy.orm import Session

from Models.ActorTagGroupModel import ActorTagGroupModel
from Models.ActorTagModel import ActorTagModel
from routers.web_data import CommonGroupForm


def getAllActorTagGroups(session: Session) -> ScalarResult[ActorTagGroupModel]:
    stmt = select(ActorTagGroupModel).order_by(
        ActorTagGroupModel.group_priority)
    return session.scalars(stmt)


def getActorTagGroup(session: Session, group_id: int) -> ActorTagGroupModel:
    return session.get(ActorTagGroupModel, group_id)


def __assign_form_to_group(group: ActorTagGroupModel, form: CommonGroupForm):
    group.group_name = form.name
    group.group_desc = form.desc
    group.group_priority = form.priority


def addNewActorTagGroup(session: Session, form: CommonGroupForm) -> ActorTagGroupModel:
    group = ActorTagGroupModel()
    __assign_form_to_group(group, form)
    session.add(group)
    session.flush()
    return group


def updateActorTagGroup(session: Session, group_id: int, form: CommonGroupForm):
    real_group: ActorTagGroupModel = session.get(ActorTagGroupModel, group_id)
    __assign_form_to_group(real_group, form)
    session.flush()
    return real_group


def deleteActorTagGroup(session: Session, group_id: int) -> bool:
    # delete the group
    session.execute(
        delete(ActorTagGroupModel).where(
            ActorTagGroupModel.group_id == group_id)
    )

    return True


def addTagToGroup(session: Session, group_id: int, tag_id: int) -> bool:
    tag = session.get(ActorTagModel, tag_id)
    if tag is None:
        return False

    if tag.tag_group_id is not None:
        if tag.tag_group_id == group_id:
            return True
        else:
            return False

    tag.tag_group_id = group_id
    session.flush()
    return True


def removeTagFromGroup(session: Session, group_id: int, tag_id: int) -> bool:
    tag = session.get(ActorTagModel, tag_id)
    if tag is None:
        return False

    if tag.tag_group_id != group_id:
        return False

    tag.tag_group_id = None
    session.flush()
    return True
