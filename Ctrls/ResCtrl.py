# Resource related operations
import re
from sqlalchemy import select, ScalarResult, update
from sqlalchemy.orm import Session

from Configs import getResSizeList
from Consts import ResState, ResType
from Models.PostModel import PostModel
from Models.ResDomainModel import ResDomainModel
from Models.ResModel import ResModel
from Models.ResUrlModel import ResUrlModel
from Models.ActorFileInfoModel import ActorFileInfoModel
from Utils import LogUtil, PyUtil
from routers.schemas_others import ResSizeCount


def getRes(session: Session, res_id: int) -> ResModel:
    """
    get a resource record by id
    """
    return session.get(ResModel, res_id)


def getResByIndex(session: Session, post_id: int, res_index: int) -> ResModel:
    """
    get a resource record by post_id and res_index
    """
    stmt = select(ResModel).where(ResModel.post_id ==
                                  post_id, ResModel.res_index == res_index)
    return session.scalar(stmt)


def getAllResUrls(session: Session, post_id: int) -> ScalarResult[ResUrlModel]:
    """
    get all resource records of a post, order by res_index
    """
    stmt = (select(ResUrlModel)
            .join(ResModel, ResUrlModel.url_id == ResModel.res_url_id)
            .where(ResModel.post_id == post_id))
    return session.scalars(stmt)


def parseResUrl(url: str) -> tuple[str, str, str]:
    match = re.match(
        r'https://([^/]+)/data/[a-f0-9]{2}/[a-f0-9]{2}/([a-f0-9]{64})\.(\w+)', url)
    if not match:
        LogUtil.error(f"无法解析资源URL: {url}")
        return None
    return match.group(1), match.group(2), match.group(3)


def getOrCreateResDomain(session: Session, domain_name: str) -> int:
    domain = session.scalar(select(ResDomainModel).where(
        ResDomainModel.domain_name == domain_name))
    if domain is None:
        domain = ResDomainModel(domain_name=domain_name)
        session.add(domain)
        session.flush()  # 获取domain.domain_id
    return domain.domain_id


def addResUrl(session: Session, url: str) -> int:
    domain_name, hash_hex, extension = parseResUrl(url)
    if domain_name is None:
        return 0

    # 获取或创建domain
    domain_id = getOrCreateResDomain(session, domain_name)

    # 创建ResUrlModel
    hash_binary = PyUtil.hex2bytes(hash_hex)
    res_url = ResUrlModel(
        domain_id=domain_id,
        hash_binary=hash_binary,
        extension=extension
    )

    session.add(res_url)
    session.flush()  # 获取res_url.url_id
    return res_url.url_id


def addAllRes(session: Session, post_id: int, url_list: list[tuple[ResType, str]]):
    for i in range(len(url_list)):
        res = ResModel()
        res.post_id = post_id
        res.res_index = i + 1
        res.res_type = url_list[i][0]
        # add res url
        url_id = addResUrl(session, url_list[i][1])
        if url_id > 0:
            res.res_url_id = url_id
        else:
            raise Exception(f"无法解析资源URL: {url_list[i][1]}")

        session.add(res)

    session.flush()


def fixResUrls(session: Session, post_id: int, url_list: list[tuple[ResType, str]], actor_name: str):
    res_url_list = getAllResUrls(session, post_id)
    res_url_dict = {res_url.hash_hex: res_url for res_url in res_url_list}

    for _, url in url_list:
        domain_name, hash_hex, extension = parseResUrl(url)
        if domain_name is None:
            continue
        if hash_hex not in res_url_dict:
            LogUtil.error(f"新增资源, {post_id} of {actor_name}, 资源URL: {url}")
            continue
        res_url = res_url_dict[hash_hex]
        new_domain_id = getOrCreateResDomain(session, domain_name)
        if res_url.domain_id != new_domain_id:
            LogUtil.info(
                f"资源域名更新, {post_id} of {actor_name}, {res_url.domain_name} to {domain_name}")
            res_url.domain_id = new_domain_id
        if res_url.extension != extension:
            LogUtil.info(
                f"资源扩展名更新, {post_id} of {actor_name}, {res_url.extension} to {extension}")
            res_url.extension = extension

    session.flush()


def getResSizesOfActor(session: Session, actor_id: int) -> list[ResSizeCount]:
    _query = (select(ResModel.res_state, ResModel.res_size)
              .join(PostModel, PostModel.post_id == ResModel.post_id)
              .where(ResModel.res_type == ResType.Video)
              .where(PostModel.actor_id == actor_id)
              .order_by(ResModel.res_size))
    ret = session.execute(_query).fetchall()
    res_size_list = getResSizeList()

    len_size = len(res_size_list)
    cur_index = 0
    cur_size = res_size_list[0]
    state_arr: list[dict[ResState, int]] = []
    state_map = {}

    for res_state, res_size in ret:
        while res_size > cur_size and cur_index < len_size:
            state_arr.append(state_map)
            state_map = {}
            cur_index += 1
            if cur_index < len_size:
                cur_size = res_size_list[cur_index]
            else:
                cur_size = -1
        state_map[res_state] = state_map.get(res_state, 0) + 1
    # fill the rest
    for index in range(cur_index, len_size + 1):
        state_arr.append(state_map)
        state_map = {}

    # print(state_arr)
    rsc_list: list[ResSizeCount] = []
    for i, state_map in enumerate(state_arr):
        item = ResSizeCount(count_map=state_map)
        if i == 0:
            item.min = 0
            item.max = res_size_list[i]
        elif i == len_size:
            item.min = res_size_list[i - 1]
            item.max = -1
        else:
            item.min = res_size_list[i - 1]
            item.max = res_size_list[i]
        rsc_list.append(item)
    return rsc_list
