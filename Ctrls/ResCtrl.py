# Resource related operations

from typing import List, Tuple

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

from Consts import ResState
from Ctrls import FileInfoCacheCtrl
from Models.BaseModel import ResModel, ResType, PostModel


def getRes(session: Session, res_id: int) -> ResModel:
    """
    get a resource record by id
    """
    return session.get(ResModel, res_id)


def getResByIndex(session: Session, post_id: int, res_index: int) -> ResModel:
    """
    get a resource record by post_id and res_index
    """
    stmt = select(ResModel).where(ResModel.post_id == post_id, ResModel.res_index == res_index)
    return session.scalar(stmt)


def getAllRes(session: Session, post_id: int) -> ScalarResult[ResModel]:
    """
    get all resource records of a post
    """
    stmt = select(ResModel).where(ResModel.post_id == post_id)
    return session.scalars(stmt)


def onResAdded(session: Session, post_id: int):
    post = session.get(PostModel, post_id)
    actor_file_info = FileInfoCacheCtrl.GetCachedFileSizes(post.actor_id)
    if actor_file_info is None:
        return
    res_list = getAllRes(session, post_id)
    for res in res_list:
        actor_file_info.addRes(res)


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
        # trim query params
        url = url_list[i][1]
        index = url.find("?")
        if index > 0:
            url = url[:index]
        res.res_url = url

        # keep other attributes as default

        session.add(res)
    session.flush()
    onResAdded(session, post_id)


def getResStatesOfActor(session: Session, actor_id: int) -> list[Tuple[ResState, int]]:
    _query = (select(ResModel.res_state)
              .where(ResModel.res_type == ResType.Video)
              .where(ResModel.post_id == PostModel.post_id)
              .where(PostModel.actor_id == actor_id)
              .order_by(ResModel.post_id.desc(), ResModel.res_index))
    ret = session.scalars(_query)
    state_list = []
    last_state = None
    last_count = 0
    for r in ret:
        if r != last_state:
            if last_state is not None:
                state_list.append((last_state, last_count))
            last_state = r
            last_count = 1
        else:
            last_count += 1
    if last_state is not None:
        state_list.append((last_state, last_count))

    return state_list
