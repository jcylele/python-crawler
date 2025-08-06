#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features
import os
import re
import ffmpeg
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

import Configs
from Ctrls import ActorCtrl, ActorFileCtrl, ResCtrl
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.NoticeModel import NoticeModel
from Models.ResModel import ResModel
from Models.ResUrlModel import ResUrlModel
from Models.PostModel import PostModel
from Models.ActorTagModel import ActorTagModel
from Utils import LogUtil


def removeActorFolders(session: Session):
    for root, folders, files in os.walk(Configs.RootFolder):
        for folder in folders:
            match_obj = re.match(r'^(\S+)_(\d+)$', folder)
            if match_obj is None:
                LogUtil.info(f"unknown folder {folder}")
                continue
            actor_id = int(match_obj.group(2))
            actor = ActorCtrl.getActor(session, actor_id)
            if actor is None:
                LogUtil.error(f"actor {actor_id} not found")
            elif not actor.actor_group.has_folder:
                LogUtil.info(f"remove folder {folder}")
                os.rmdir(os.path.join(root, folder))

def refreshResInfo(session: Session):
    for root1, folders, _ in os.walk(Configs.RootFolder):
        for folder in folders:
            match_obj1 = re.match(r'^(\S+)_(\d+)$', folder)
            if match_obj1 is None:
                LogUtil.info(f"unknown folder {folder}")
                continue
            actor_name = match_obj1.group(1)
            for root2, _, files in os.walk(os.path.join(root1, folder)):
                for file in files:
                    match_obj2 = re.match(r'^(\d+)_(\d+)\.(\S+)$', file)
                    if match_obj2 is None:
                        LogUtil.error(f"unknown file {file}")
                        continue
                    post_id = int(match_obj2.group(1))
                    res_index = int(match_obj2.group(2))
                    extension = match_obj2.group(3)
                    # skip image files
                    if extension == 'jpg' or extension == 'jpeg':
                        continue
                    res = ResCtrl.getResByIndex(session, post_id, res_index)
                    if res is None:
                        LogUtil.error(f"res {post_id}_{res_index} not found")
                        continue
                    file_path = os.path.join(root2, file)
                    width, height, duration = ActorFileCtrl.get_media_info(file_path)
                    if width > 0 and height > 0:
                        res.res_width = width
                        res.res_height = height
                        if duration > 0:
                            res.res_duration = duration
            print(actor_name)
            session.flush()

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


def get_tag_combinations_with_empty(session: Session) -> list[dict]:
    # 首先获取带标签的组合
    subq = (
        select(
            ActorTagRelationship.main_actor_id,
            func.group_concat(
                ActorTagRelationship.tag_id.op('ORDER BY')(
                    ActorTagRelationship.tag_id
                )
            ).label('tag_ids')
        )
        .group_by(ActorTagRelationship.main_actor_id)
        .subquery()
    )

    # 使用左连接来包含没有标签的 main_actor
    query = (
        select(
            subq.c.tag_ids,
            func.count(ActorMainModel.main_actor_id).label('count')
        )
        .select_from(ActorMainModel)
        .outerjoin(subq, ActorMainModel.main_actor_id == subq.c.main_actor_id)
        .group_by(subq.c.tag_ids)
        .order_by(func.count(ActorMainModel.main_actor_id).desc())
        .limit(20)
    )

    results = []
    for row in session.execute(query):
        if row.tag_ids is None:
            # 无标签的情况
            tag_combination = {
                'tag_ids': [],
                'count': row.count,
                'has_tags': False
            }
        else:
            # 有标签的情况
            tag_ids = [int(x) for x in row.tag_ids.split(',')]
            tag_combination = {
                'tag_ids': tag_ids,
                'count': row.count,
                'has_tags': True
            }
        results.append(tag_combination)

    return results


def validateActor(session: Session, actor_id: int):
    actor = ActorCtrl.getActor(session, actor_id)
    # set res state to downed if downloaded files exist
    ActorFileCtrl.traverseDownloadedFilesOfActor(session, actor, ActorCtrl._setResStateToDowned)