# Resource related operations

from typing import List, Tuple

from sqlalchemy import select, ScalarResult
from sqlalchemy.orm import Session

from Configs import RES_SIZE_LIST
from Consts import ResState, ResType
from Ctrls import FileInfoCacheCtrl
from Models.PostModel import PostModel
from Models.ResModel import ResModel
from Models.ResSizeCount import ResSizeCount


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


def getResSizesOfActor(session: Session, actor_id: int) -> list[ResSizeCount]:
    _query = (select(ResModel.res_state, ResModel.res_size)
              .where(ResModel.res_type == ResType.Video)
              .where(ResModel.post_id == PostModel.post_id)
              .where(PostModel.actor_id == actor_id)
              .order_by(ResModel.res_size))
    ret = session.execute(_query).fetchall()

    len_size = len(RES_SIZE_LIST)
    cur_index = 0
    cur_size = RES_SIZE_LIST[0]
    state_arr: list[dict[ResState, int]] = []
    state_map = {}

    for res_state, res_size in ret:
        while res_size > cur_size and cur_index < len_size:
            state_arr.append(state_map)
            state_map = {}
            cur_index += 1
            if cur_index < len_size:
                cur_size = RES_SIZE_LIST[cur_index]
            else:
                cur_size = -1
        state_map[res_state] = state_map.get(res_state, 0) + 1
    # fill the rest
    for index in range(cur_index, len_size + 1):
        state_arr.append(state_map)
        state_map = {}

    # print(state_arr)
    rsc_list: List[ResSizeCount] = []
    for i, state_map in enumerate(state_arr):
        item = ResSizeCount()
        item.setStateMap(state_map)
        if i == 0:
            item.min = 0
            item.max = RES_SIZE_LIST[i]
        elif i == len_size:
            item.min = RES_SIZE_LIST[i - 1]
            item.max = -1
        else:
            item.min = RES_SIZE_LIST[i - 1]
            item.max = RES_SIZE_LIST[i]
        rsc_list.append(item)
    return rsc_list
