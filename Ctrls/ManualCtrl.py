#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features
import os
import re
import random

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

import Configs
from Ctrls import ActorCtrl, DbCtrl, ResCtrl
from Models.ActorTagModel import ActorTagModel
from Models.ResDomainModel import ResDomainModel
from Models.ResModel import ResModel
from Models.ActorModel import ActorModel
from Models.ResUrlModel import ResUrlModel
from Utils import LogUtil, PyUtil


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
