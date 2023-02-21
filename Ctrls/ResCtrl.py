# Resource related operations

import os
from typing import List, Tuple

from sqlalchemy import select, ScalarResult, delete
from sqlalchemy.orm import Session

from Models.BaseModel import ResModel, ResState, ResType


def getRes(session: Session, res_id: int) -> ResModel:
    """
    get a resource record by id
    """
    return session.get(ResModel, res_id)


def getAllRes(session: Session, post_id: int) -> ScalarResult[ResModel]:
    """
    get all resource records of a post
    """
    stmt = select(ResModel).where(ResModel.post_id == post_id)
    return session.scalars(stmt)


def addAllRes(session: Session, post_id: int, url_list: List[Tuple[ResType, str]]):
    """
    add resource records of a post
    :param session:
    :param post_id:
    :param url_list: [(resource type, url of the resource)]
    :return:
    """
    for i in range(len(url_list)):
        res = ResModel()
        res.post_id = post_id
        res.res_index = i + 1
        res.res_type = url_list[i][0]
        res.res_url = url_list[i][1]
        # keep other attributes as default

        session.add(res)


def repairRecords(session: Session):
    """
    refresh the state of a resource record if corresponding file is deleted
    :TODO full traverse if time consuming, should be optimized
    """
    stmt = select(ResModel).where(ResModel.res_state == ResState.Down)
    result: ScalarResult[ResModel] = session.scalars(stmt)
    for res in result:
        file_path = res.filePath()
        if not os.path.exists(file_path):
            res.res_state = ResState.Del
