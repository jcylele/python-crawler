#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features
import os
import re
from collections import defaultdict
from typing import List, Dict, Set, Tuple

from sqlalchemy import func, select
from sqlalchemy import update
from sqlalchemy.orm import Session
from starlette.config import undefined

import Configs
from Consts import ResState, NoticeType
from Ctrls import ActorCtrl
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.ActorTagModel import ActorTagModel
from Models.NoticeModel import NoticeModel
from Models.PostModel import PostModel
from Models.ResModel import ResModel
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


def checkNotice(session, notice_id):
    notice:NoticeModel = session.get(NoticeModel, notice_id)
    notice.check()
