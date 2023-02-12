import os
import re
from typing import List, Tuple

from sqlalchemy import select, ScalarResult, delete
from sqlalchemy.orm import Session

import Consts
import LogUtil
from Ctrls import CtrlUtil
from Models.BaseModel import ResModel, ResState, ResType


def getRes(session: Session, res_id: int) -> ResModel:
    return session.get(ResModel, res_id)


def getAllRes(session: Session, post_id: int) -> ScalarResult[ResModel]:
    stmt = select(ResModel).where(ResModel.post_id == post_id)
    return session.scalars(stmt)


def delAllRes(session: Session, post_id: int):
    stmt = (
        delete(ResModel)
            .where(ResModel.post_id == post_id)
    )
    session.execute(stmt)


def addAllRes(session: Session, post_id: int, url_list: List[Tuple[bool, str]]):
    for i in range(len(url_list)):
        res = ResModel()
        res.post_id = post_id
        res.res_url = url_list[i][1]
        res.res_index = i + 1
        res.res_state = ResState.Init
        if url_list[i][0]:
            res.res_type = ResType.Image
        else:
            res.res_type = ResType.Video
        session.add(res)


def removeInvalidRes(session: Session):
    stmt = select(ResModel).where(ResModel.res_state == ResState.Down)
    result: ScalarResult[ResModel] = session.scalars(stmt)
    for res in result:
        file_path = res.filePath()
        if not os.path.exists(file_path):
            LogUtil.warn(f"{file_path} file not found")

        real_size = os.path.getsize(file_path)
        if real_size < res.res_size:
            LogUtil.warn(f"{file_path} incorrect size, expect {res.res_size:,d} get {real_size:,d}")
            os.remove(file_path)
            res.res_state = ResState.Init


def repairRecords(session: Session):
    """
    已下载的资源如果不存在了，说明删除了
    (Dislike角色的所有资源先前已经都删除了)
    """
    stmt = select(ResModel).where(ResModel.res_state == ResState.Down)
    result: ScalarResult[ResModel] = session.scalars(stmt)
    for res in result:
        file_path = res.filePath()
        if not os.path.exists(file_path):
            res.res_state = ResState.Del
