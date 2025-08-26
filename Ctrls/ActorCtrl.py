# ActorModel related operations
from collections.abc import Iterable

from sqlalchemy import delete, exists, select, event, inspect
from sqlalchemy.orm import Session

from Consts import ErrorCode, NoticeType, ActorLogType, ResState
from Ctrls import DbCtrl, PostCtrl, ResCtrl, ActorGroupCtrl, NoticeCtrl, ActorLogCtrl, ActorFileCtrl, ResFileCtrl
from Models.ActorInfo import ActorInfo
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.PostModel import PostModel
from Utils import LogUtil, PyUtil


# region single actor


def getActorInfo(session: Session, actor_id: int) -> ActorInfo:
    actor = getActor(session, actor_id)
    if actor is None:
        LogUtil.error(f"get actorInfo failed, actor {actor_id} not exist")
        return None
    return ActorInfo(actor)


def getActor(session: Session, actor_id: int) -> ActorModel:
    return session.get(ActorModel, actor_id)


def getActors(session: Session, actor_ids: list[int]) -> list[ActorModel]:
    return list(session.scalars(select(ActorModel).where(ActorModel.actor_id.in_(actor_ids))))


def getMainActor(session: Session, main_actor_id: int) -> ActorMainModel:
    return session.get(ActorMainModel, main_actor_id)


def getActorByInfo(session: Session, actor_info: ActorInfo) -> ActorModel:
    _query = select(ActorModel) \
        .where(ActorModel.actor_name == actor_info.actor_name) \
        .where(ActorModel.actor_platform == actor_info.actor_platform)
    return session.scalar(_query)


def getActorsByName(session: Session, actor_name: str) -> list[ActorModel]:
    query = select(ActorModel).where(
        ActorModel.actor_name == actor_name)
    return list(session.scalars(query))


def checkSameActorName(session: Session, actor_name: str):
    exists_query = select(exists().where(
        ActorModel.actor_name == actor_name
    ))
    name_exists = session.scalar(exists_query)
    if name_exists:
        NoticeCtrl.addNotice(session, NoticeType.SameActorName, actor_name)


def addActor(session: Session, actor_info: ActorInfo, group_id: int) -> ActorModel:
    checkSameActorName(session, actor_info.actor_name)

    actor = ActorModel(actor_name=actor_info.actor_name,
                       actor_platform=actor_info.actor_platform,
                       actor_link=actor_info.actor_link,
                       actor_group_id=group_id)
    session.add(actor)
    session.flush()  # ensure actor_id is set

    # add main_actor
    main_actor = ActorMainModel(
        main_actor_id=actor.actor_id
    )
    session.add(main_actor)
    # set main_actor_id to self
    actor.main_actor_id = actor.actor_id
    session.flush()

    ActorLogCtrl.addActorLog(session, actor.actor_id, ActorLogType.Add)
    ActorFileCtrl.createActorFolder(actor)

    return actor

# endregion


# region update actor / main_actor


def _innerSetActorTags(session: Session, main_actor_id: int, tag_list: Iterable[int]):
    # delete all old tags
    _query = delete(ActorTagRelationship) \
        .where(ActorTagRelationship.main_actor_id == main_actor_id)
    session.execute(_query)

    # add new tags
    for tag_id in tag_list:
        rel_tag = ActorTagRelationship(
            tag_id=tag_id,
            main_actor_id=main_actor_id
        )
        session.add(rel_tag)


def changeActorTags(session: Session, actor_id: int, tag_list: list[int]) -> list[ActorModel]:
    # set tags for main_actor
    actor = getActor(session, actor_id)
    _innerSetActorTags(session, actor.main_actor_id, tag_list)

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Tag, *tag_list)

    session.flush()
    return linked_actors


def changeActorScore(session: Session, actor_id: int, score: int) -> list[ActorModel]:
    # change score for main_actor
    actor = getActor(session, actor_id)
    main_actor = actor.main_actor
    if main_actor.score == score:
        return []  # no change
    # set field
    main_actor.score = score

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Score, score)

    session.flush()
    return linked_actors


def changeActorComment(session: Session, actor_id: int, comment: str) -> ActorModel:
    # change comment for main_actor
    actor = getActor(session, actor_id)
    actor.comment = comment
    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.Comment, comment)
    session.flush()
    return actor


def changeActorRemark(session: Session, actor_id: int, remark: str) -> list[ActorModel]:
    # process remark
    real_remark = PyUtil.stripToNone(remark)
    # change remark for main_actor
    actor = getActor(session, actor_id)
    main_actor: ActorMainModel = actor.main_actor

    if main_actor.remark == real_remark:
        return []  # no change

    # set field
    main_actor.remark = real_remark

    # add log for linked actors
    linked_actors = getLinkedActors(session, actor.main_actor_id)
    for linked_actor in linked_actors:
        ActorLogCtrl.addActorLog(
            session, linked_actor.actor_id, ActorLogType.Remark, remark)

    session.flush()
    return linked_actors


def _setResStateToDowned(session: Session, file_path: str, post_id: int, res_index: int):
    res = ResCtrl.getResByIndex(session, post_id, res_index)
    if res is None:
        return
    res.res_state = ResState.Down


def resetActorPosts(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    actor.last_post_id = 0

    PostCtrl.batchSetResStates(session, actor_id, ResState.Init)
    # set res state to downed if downloaded files exist
    ResFileCtrl.traverseDownloadedFilesOfActor(
        session, actor, _setResStateToDowned)

    ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.ResetPost)


def changeActorGroup(session: Session, actor_id: int, new_group_id: int) -> tuple[ErrorCode, ActorModel]:
    actor = getActor(session, actor_id)
    # no change
    if actor.actor_group_id == new_group_id:
        return ErrorCode.GroupAlreadyIn, actor
    # check group condition
    cond_id = ActorGroupCtrl.checkGroupCondition(
        session, actor, new_group_id)
    if cond_id != 0:
        return ErrorCode.GroupCondFailed, actor

    oldHas = actor.actor_group.has_folder
    new_group = ActorGroupCtrl.getActorGroup(session, new_group_id)
    newHas = new_group.has_folder
    if oldHas != newHas:
        if oldHas:
            ActorFileCtrl.deleteAllRes(session, actor)
            last_post_id = PostCtrl.getMaxPostId(session, actor_id)
            actor.last_post_id = last_post_id
        else:
            ActorFileCtrl.createActorFolder(actor)

    # set field
    actor.setGroup(new_group_id)
    session.flush()

    ActorLogCtrl.addActorLog(
        session, actor_id, ActorLogType.Group, new_group_id)

    return ErrorCode.Success, actor


# endregion

# region linked related, have to be here because of circular import

def getLinkedActors(session: Session, main_actor_id: int) -> list[ActorModel]:
    stmt = (
        select(ActorModel)
        .where(ActorModel.main_actor_id == main_actor_id)
        .order_by(ActorModel.actor_group_id, ActorModel.actor_name)
    )
    return list(session.scalars(stmt))


def getLinkedActorIds(session: Session, main_actor_id: int) -> list[int]:
    stmt = (
        select(ActorModel.actor_id)
        .where(ActorModel.main_actor_id == main_actor_id)
        .order_by(ActorModel.actor_group_id, ActorModel.actor_name)
    )
    return list(session.scalars(stmt))

# endregion

# region post related


def refreshActorPostCount(session: Session, actor_id: int):
    actor = getActor(session, actor_id)
    completed, uncompleted = PostCtrl.getPostCountsOfActor(session, actor_id)
    actor.current_post_count = completed + uncompleted
    actor.completed_post_count = completed


def fixPostBelong(session: Session, post: PostModel, old_owner: ActorModel, new_owner: ActorModel):
    LogUtil.info(
        f"fix post {post.post_id} belong changed from {old_owner.actor_name} to {new_owner.actor_name}")
    post.actor_id = new_owner.actor_id
    # update post counts
    old_owner.current_post_count -= 1
    new_owner.current_post_count += 1
    if post.completed:
        old_owner.completed_post_count -= 1
        new_owner.completed_post_count += 1
        # actor file info should be refreshed
        ActorFileCtrl.deleteActorFileInfos(
            [old_owner.actor_id, new_owner.actor_id])

    # actors should be linked
    if new_owner.main_actor_id != old_owner.main_actor_id:
        NoticeCtrl.addNoticeStrict(session, NoticeType.UnlinkedActor,
                                   [new_owner.actor_name, old_owner.actor_name])
        LogUtil.error(
            f"same post {post.post_id} for {new_owner.actor_name} and {old_owner.actor_name}")


def _updateActorPostCount(session: Session, actor_id: int, post_completed: bool, delta: int):
    actor = getActor(session, actor_id)
    actor.current_post_count += delta
    if post_completed:
        actor.completed_post_count += delta


@event.listens_for(PostModel, 'after_insert')
def after_post_insert(mapper, connection, target: PostModel):
    with DbCtrl.newSession(connection) as session, session.begin():
        _updateActorPostCount(session, target.actor_id, target.completed, 1)


@event.listens_for(PostModel, 'after_delete')
def after_post_delete(mapper, connection, target: PostModel):
    with DbCtrl.newSession(connection) as session, session.begin():
        _updateActorPostCount(session, target.actor_id, target.completed, -1)


def _updateCompletedPostCount(session: Session, actor_id: int, delta: int):
    actor = getActor(session, actor_id)
    actor.completed_post_count += delta


@event.listens_for(PostModel, 'after_update')
def after_post_update(mapper, connection, target: PostModel):
    # 检查 'completed' 字段是否发生变化
    history = inspect(target).attrs.completed.history
    if not history.has_changes():
        return

    delta = 0
    if history.added[0] and not history.deleted[0]:  # False -> True
        delta = 1
    elif not history.added[0] and history.deleted[0]:  # True -> False
        delta = -1
    else:
        return

    with DbCtrl.newSession(connection) as session, session.begin():
        _updateCompletedPostCount(session, target.actor_id, delta)

# endregion
