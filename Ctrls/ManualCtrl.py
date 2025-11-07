#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features
import os
import re
import shutil
import aiofiles
import aiohttp
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

import Configs
from Consts import NoticeType
from Ctrls import ActorCtrl, ActorFileCtrl, ActorSimilarCtrl, RequestCtrl, ResCtrl, ResFileCtrl
from Models.FavoriteFolderModel import FavoriteFolderModel
from Models.ActorGroupModel import ActorGroupModel
from Models.ActorFileInfoModel import ActorFileInfoModel
from Models.ActorTagGroupModel import ActorTagGroupModel
from Models.ActorMainModel import ActorMainModel
from Models.ActorModel import ActorModel
from Models.ActorTagModel import ActorTagModel
from Models.ActorTagRelationship import ActorTagRelationship
from Models.NoticeModel import NoticeModel
from Models.ResModel import ResModel
from Utils import LogUtil


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


async def check_size(session: Session, file_path: str, res_id: int):
    res = session.get(ResModel, res_id)
    if await aiofiles.os.path.exists(file_path):
        file_size = (await aiofiles.os.stat(file_path)).st_size
        print(file_size == res.res_size, file_size)


def renameThumbnailFolder(session: Session):
    with os.scandir(Configs.getRootFolder()) as it1:
        for entry1 in it1:
            if entry1.is_file():
                continue
            match_obj = re.match(r'^(\S+)_(\d+)$', entry1.name)
            if match_obj is None:
                continue
            actor_name = match_obj.group(1)
            with os.scandir(entry1.path) as it2:
                for entry2 in it2:
                    if entry2.is_file():
                        continue
                    if entry2.name == Configs.ThumbnailFolder:
                        os.rename(entry2.path, os.path.join(
                            entry1.path, f"_{actor_name}"))


def printResUrl(session: Session):
    stmt = select(ResModel).where(ResModel.post_id == 762440076)
    res = session.scalar(stmt)
    print(res.res_url_info.full_url)


async def testRedirect(url: str):
    requestSession = aiohttp.ClientSession()
    headers = RequestCtrl.createRequestHeaders()
    # headers["referer"] = item.from_url
    try:
        async with requestSession.head(url, headers=headers, allow_redirects=False) as res:
            if res.status == 200:
                content_length = res.headers.get('Content-Length')
                print(content_length or 0)
            elif res.status in (301, 302, 307, 308):  # redirect
                url = res.headers['Location']
                new_url = RequestCtrl.formatFullUrl(url)
                print(new_url)
            else:
                print(res.status, res.url)
    except Exception as e:
        print("Error:")
        print(e)

def fixNotice(session: Session):
    stmt = select(NoticeModel).where(NoticeModel.notice_type == NoticeType.InvalidPost)
    notices = session.scalars(stmt)
    for notice in notices:
        notice.refreshChecksum()