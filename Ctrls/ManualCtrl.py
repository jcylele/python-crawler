#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features

import os
import re

from sqlalchemy import select, update
from sqlalchemy.orm import Session

import Configs
from Consts import NoticeType
from Ctrls import ActorCtrl, PostCtrl, NoticeCtrl
from Models.BaseModel import ActorModel, ActorGroupModel, NoticeModel
from Utils import LogUtil


def removeActorFolders(session: Session):
    for root, folders, files in os.walk(Configs.RootFolder):
        for folder in folders:
            matchObj = re.match(r'^(\S+)_(\d+)$', folder)
            if matchObj is None:
                LogUtil.info(f"unknown folder {folder}")
                continue
            actor_id = int(matchObj.group(2))
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None:
                LogUtil.error(f"actor {actor_id} not found")
            elif not actor.actor_group.has_folder:
                LogUtil.info(f"remove folder {folder}")
                os.rmdir(os.path.join(root, folder))


def RelinkActors(session: Session):
    """
    synchronize linked actors' score, tags by relinking them
    :param session:
    :return:
    """
    stmt1 = (select(ActorModel.main_actor_id.distinct()))
    main_list = session.scalars(stmt1)
    for main_actor_id in main_list:
        if main_actor_id == 0:
            continue
        stmt2 = (
            select(ActorModel.actor_id)
            .where(ActorModel.main_actor_id == main_actor_id)
        )
        actor_ids = session.scalars(stmt2)
        actor_ids = [a for a in actor_ids]
        ActorCtrl.linkActors(session, actor_ids)


def RenameActorFolders(session: Session):
    """
    rename actor folders from {actor_name} to {actor_name}_{actor_id}
    """
    for root, folders, files in os.walk(Configs.RootFolder):
        for folder in folders:
            actors = ActorCtrl.getActorsByName(session, folder)
            if len(actors) > 1:
                for actor in actors:
                    ActorCtrl.createActorFolder(actor)
                old_folder = os.path.join(root, folder)
                for actor_root, _, res_files in os.walk(old_folder):
                    for res_file in res_files:
                        matchObj = re.match(r'^(\d+)_(\d+)\.\w+$', res_file)
                        if matchObj is None:
                            continue
                        post_id = int(matchObj.group(1))
                        post = PostCtrl.getPost(session, post_id)
                        actor = post.actor
                        actor_folder = Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)
                        os.rename(os.path.join(actor_root, res_file), os.path.join(actor_folder, res_file))
                os.rmdir(old_folder)
            elif len(actors) == 1:
                new_name = folder + "_" + str(actors[0].actor_id)
                os.rename(os.path.join(root, folder), os.path.join(root, new_name))
            else:
                print(f"unknown folder {folder}")


def FindUnMatchedActors(session: Session):
    """
    find linked actors in unmatched groups
    """
    stmt = (
        select(ActorModel.main_actor_id, ActorGroupModel.group_id)
        .where(ActorModel.actor_group_id == ActorGroupModel.group_id)
        .where(ActorModel.main_actor_id != 0)
        .where(ActorGroupModel.has_folder == False)
    )

    actor_group_dict = {}
    actor_ids = set()
    ret = session.execute(stmt).fetchall()
    for main_actor_id, group_id in ret:
        if main_actor_id in actor_group_dict:
            if actor_group_dict[main_actor_id] != group_id:
                actor_ids.add(main_actor_id)
        else:
            actor_group_dict[main_actor_id] = group_id

    for main_actor_id in actor_ids:
        stmt2 = (
            select(ActorModel)
            .where(ActorModel.main_actor_id == main_actor_id)
        )
        actor_list = session.scalars(stmt2)
        names = [actor.actor_name for actor in actor_list]
        print(f"{main_actor_id} {names}")


def RenameIconExtension(session: Session):
    for root, _, files in os.walk(Configs.formatIconFolderPath()):
        for file in files:
            old_file_path = os.path.join(root, file)
            matchObj = re.match(r'^(\S+)\.jfif$', file)
            if matchObj is None:
                continue

            pure_name = matchObj.group(1)
            new_file_name = f"{pure_name}.png"
            os.rename(old_file_path, os.path.join(root, new_file_name))


def RenameIcons(session: Session):
    for root, _, files in os.walk(Configs.formatIconFolderPath()):
        for file in files:
            old_file_path = os.path.join(root, file)
            matchObj = re.match(r'^(\S+)\.jfif$', file)
            if matchObj is None:
                print(f"unknown file {file}")
                os.remove(old_file_path)
                continue

            actor_name = matchObj.group(1)
            actors = ActorCtrl.getActorsByName(session, actor_name)
            if len(actors) == 0:
                print(f"actor {actor_name} not found")
                os.remove(old_file_path)
            elif len(actors) == 1:
                actor = actors[0]
                new_file_name = f"{actor.actor_name}_{actor.actor_platform}.jfif"
                print(f"rename {file} to {new_file_name}.jfif")
                os.rename(old_file_path, os.path.join(root, new_file_name))
            else:
                print(f"multiple actors of {actor_name}")
                os.remove(old_file_path)


def resetManual(session: Session):
    stmt = (
        update(ActorModel)
        .values(manual_done=False)
    )
    session.execute(stmt)


def getManualActorIds(session: Session, limit: int, offset: int = 0) -> list[int]:
    stmt = (
        select(ActorModel.actor_id)
        .where(ActorModel.manual_done == False)
        .order_by(ActorModel.actor_name)
    )
    if limit != 0:
        stmt = stmt.limit(limit)
    if offset != 0:
        stmt = stmt.offset(offset)
    actor_ids = session.scalars(stmt)
    return [a for a in actor_ids]


def reChecksumAllNotices(session: Session):
    for nt in NoticeType:
        stmt = (select(NoticeModel)
                .filter(NoticeModel.notice_type == nt))
        result = session.scalars(stmt)
        for notice in result:
            notice.refreshChecksum()

def reorderNoticeParams(session: Session, notice_type: NoticeType):
    stmt = (select(NoticeModel)
            .filter(NoticeModel.notice_type == notice_type))
    result = session.scalars(stmt)
    for notice in result:
        names = NoticeCtrl.sortedDistinctNames([notice.notice_param0, notice.notice_param1, notice.notice_param2, notice.notice_param3])
        for i in range(4):
            if i < len(names):
                setattr(notice, f"notice_param{i}", names[i])
            else:
                setattr(notice, f"notice_param{i}", "")
        notice.refreshChecksum()