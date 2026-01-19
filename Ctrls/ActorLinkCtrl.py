from sqlalchemy import delete, select, func, update
from sqlalchemy.orm import Session

from Consts import ActorLogType, ErrorCode, NoticeType
from Ctrls import ActorCtrl, ActorLogCtrl, CommonCtrl, NoticeCtrl
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.Exceptions import BusinessException
from Utils import LogUtil
from routers.web_data import LinkActorForm


def _distinct(id_list: list[int]) -> list[int]:
    return list(set(id_list))


def unlinkActors(session: Session, actor_ids: list[int]):
    actor_ids = _distinct(actor_ids)
    # check all actors belong to the same group, and all actors in the group are selected
    actor_list = [CommonCtrl.getActor(session, actor_id)
                  for actor_id in actor_ids]
    main_actor_id = 0
    for actor in actor_list:
        if not actor.is_linked:  # not linked
            raise BusinessException(ErrorCode.UnlinkedActor)
        if main_actor_id == 0:
            main_actor_id = actor.main_actor_id
        elif main_actor_id != actor.main_actor_id:  # not in same link
            raise BusinessException(ErrorCode.MultiLinkGroups)

    # check if all actors included
    stmt = select(func.count(ActorModel.actor_id)).where(
        ActorModel.main_actor_id == main_actor_id)
    linked_actor_count = session.scalar(stmt)
    if linked_actor_count > len(actor_ids):
        raise BusinessException(ErrorCode.NotAllLinkedActors)

    main_actor = ActorCtrl.getMainActor(session, main_actor_id)
    if main_actor is None:
        raise BusinessException(ErrorCode.MainActorNotFound)

    for actor in actor_list:
        # copy main_actor
        new_main_actor = ActorMainModel(
            main_actor_id=actor.actor_id,
            remark=main_actor.remark,
            score=main_actor.score
        )

        rel_tags = []
        # copy rel_tags
        for rel_tag in main_actor.rel_tags:
            new_rel_tag = ActorTagRelationship(
                tag_id=rel_tag.tag_id,
                main_actor_id=actor.actor_id
            )
            rel_tags.append(new_rel_tag)

        new_main_actor.rel_tags = rel_tags
        session.add(new_main_actor)

        # set main_actor_id to self
        actor.main_actor_id = actor.actor_id
        # add log
        ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Unlink)

    # delete main_actor, rel_tags will be deleted by cascade
    session.delete(main_actor)

    session.flush()


def linkActors(session: Session, form: LinkActorForm):
    actor_ids = _distinct(form.actor_ids)
    # check all actors belong to the same link group or no group
    actor_list = [CommonCtrl.getActor(session, actor_id)
                  for actor_id in actor_ids]
    # will be removed at the end
    old_main_actor_ids = set()
    for actor in actor_list:
        old_main_actor_ids.add(actor.main_actor_id)

    # check all linked actors are included
    stmt = select(func.count(ActorModel.actor_id)).where(
        ActorModel.main_actor_id.in_(old_main_actor_ids))
    total_linked_actor_count = session.scalar(stmt)
    if total_linked_actor_count > len(actor_ids):
        raise BusinessException(ErrorCode.NotAllLinkedActors)

    # choose a new main_actor_id from actor_ids, exclude old ones
    new_main_actor_id = 0
    for actor_id in actor_ids:
        if (-actor_id) not in old_main_actor_ids:
            new_main_actor_id = -actor_id
            break
    if new_main_actor_id == 0:
        raise BusinessException(ErrorCode.NoNewMainActor)

    # create a new main_actor
    new_main_actor = ActorMainModel(
        main_actor_id=new_main_actor_id,
        remark=form.remark,
        score=form.score
    )

    rel_tags = []
    for tag_id in form.tag_list:
        rel_tag = ActorTagRelationship(
            tag_id=tag_id,
            main_actor_id=new_main_actor_id
        )
        rel_tags.append(rel_tag)
    # add new_main_actor along with rel_tags
    new_main_actor.rel_tags = rel_tags
    session.add(new_main_actor)

    actor_names = [actor.actor_name for actor in actor_list]
    # apply link
    for actor in actor_list:
        actor.main_actor_id = new_main_actor_id
        ActorLogCtrl.addActorLog(
            session, actor.actor_id, ActorLogType.Link, *actor_names)
        if form.score != 0:
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Score, form.score)
        if form.remark != "":
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Remark, form.remark)
        if len(form.tag_list) > 0:
            ActorLogCtrl.addActorLog(
                session, actor.actor_id, ActorLogType.Tag, *form.tag_list)

    # flush to ensure old_main_actor_ids are not ref by actors now
    session.flush()

    # remove old main_actors along with rel_tags
    stmt = delete(ActorMainModel).where(
        ActorMainModel.main_actor_id.in_(old_main_actor_ids))
    session.execute(stmt)
    session.flush()



def getGroupsOfLinkedActors(session: Session, actor_id: int) -> list[int]:
    actor = CommonCtrl.getActor(session, actor_id)
    if not actor.is_linked:
        return [actor.actor_group_id]

    stmt = (
        select(ActorModel.actor_group_id)
        .where(ActorModel.main_actor_id == actor.main_actor_id)
        .order_by(ActorModel.actor_group_id)
    )
    return list(session.scalars(stmt))


def isLinkChecked(session: Session, actor_id: int):
    actor = CommonCtrl.getActor(session, actor_id)
    return actor.link_checked


def setActorLinkChecked(session: Session, actor_id: int):
    stmt = (
        update(ActorModel)
        .where(ActorModel.actor_id == actor_id)
        .values(link_checked=True)
    )
    session.execute(stmt)


def checkActorLink(session, actor_ids: list[int]):
    actor_list = [CommonCtrl.getActor(session, actor_id)
                  for actor_id in actor_ids]
    actor_list.sort(key=lambda x: x.actor_name)
    main_actor_ids = set()
    for actor in actor_list:
        main_actor_ids.add(actor.main_actor_id)

    if len(main_actor_ids) > 1 or (0 in main_actor_ids):
        actor_names = [actor.actor_name for actor in actor_list]
        NoticeCtrl.addNoticeStrict(
            session, NoticeType.HasLinkedAccount, actor_names)
    else:
        actor_names = ",".join([actor.actor_name for actor in actor_list])
        LogUtil.info(f"actors already linked: {actor_names}")

    for actor in actor_list:
        actor.link_checked = True
