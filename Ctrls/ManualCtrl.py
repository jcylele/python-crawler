#! fix/update bugs/problems in database, mainly caused by existing actors skipping new features
import os
import re
import shutil
import aiofiles
import aiohttp
from imagehash import ImageHash, hex_to_hash
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

import Configs
from Consts import NoticeType, ResState
from Ctrls import ActorCtrl, ActorFileCtrl, ActorSimilarCtrl, CommonCtrl, RequestCtrl, ResCtrl, ResFileCtrl, WatermarkCtrl
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
from Utils import LogUtil, PyUtil


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
    stmt = select(NoticeModel).where(
        NoticeModel.notice_type == NoticeType.InvalidPost)
    notices = session.scalars(stmt)
    for notice in notices:
        notice.refreshChecksum()


def allPureNames(session: Session):
    stmt = select(ActorModel.actor_name).where(ActorModel.actor_group_id != 3)
    actor_names = session.scalars(stmt)
    all_pure_names = set()
    for actor_name in actor_names:
        pure_name = ActorSimilarCtrl._possible_pure_name(actor_name)
        if pure_name is not None:
            all_pure_names.add(pure_name)

    sorted_list = sorted(all_pure_names)
    with open(os.path.join(Configs.getRootFolder(), "pure_names.txt"), "w", encoding="utf-8") as f:
        for pure_name in sorted_list:
            f.write(pure_name + "\n")


def differ_icon(session: Session):
    actor_ids = [14799, 11852]
    icon_hashes = []
    for actor_id in actor_ids:
        stmt = select(ActorModel.icon_hash).where(
            ActorModel.actor_id == actor_id)
        icon_hash = session.scalar(stmt)
        icon_hashes.append(int(icon_hash, 16))
    for hash in icon_hashes:
        print(hex(hash))


def rename_downloading_files(session: Session):
    download_folder = Configs.formatDownloadingFolderPath()
    try:
        with os.scandir(download_folder) as it:
            for entry in it:
                match_obj = re.match(r'^(.+)_(\d+)_(\d+)\.(\w+)$', entry.name)
                if match_obj is None:
                    continue
                post_id = int(match_obj.group(2))
                res_index = int(match_obj.group(3))

                post = CommonCtrl.getPost(session, post_id)
                res = ResCtrl.getResByIndex(session, post_id, res_index)

                new_file_name = f"{post.actor_id}_{post_id}_{res.res_id}.{match_obj.group(4)}"
                os.rename(entry.path, os.path.join(
                    os.path.dirname(entry.path), new_file_name))

    except Exception as e:
        LogUtil.error(f"traverseDownloadingFiles failed, get Error")
        LogUtil.exception(e)
        pass


def favorite_count_inversions(session: Session):
    stmt = (select(ActorModel.favorite_count)
            .where(ActorModel.favorite_count != 0)
            .order_by(ActorModel.actor_id.desc()))
    counts = [c for c in session.scalars(stmt)]
    inversions = count_inversions_merge_optimized(counts)
    print(f"inversions: {inversions}")
    print(f"counts: {len(counts)}")


def count_inversions_merge_optimized(arr):
    """
    优化的归并排序统计逆序数
    对基本有序数组有优化，最坏情况 O(n log n)
    """
    def merge_and_count(left, right):
        result = []
        inversions = 0
        i = j = 0

        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                inversions += len(left) - i
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])
        return result, inversions

    def merge_sort_and_count(arr):
        if len(arr) <= 1:
            return arr, 0

        # 对于小数组，使用插入排序可能更快
        if len(arr) <= 10:
            return insertion_sort_and_count(arr)

        mid = len(arr) // 2
        left, left_inv = merge_sort_and_count(arr[:mid])
        right, right_inv = merge_sort_and_count(arr[mid:])
        merged, merge_inv = merge_and_count(left, right)

        return merged, left_inv + right_inv + merge_inv

    def insertion_sort_and_count(arr):
        """小数组使用插入排序"""
        count = 0
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                count += 1
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr, count

    arr_copy = arr.copy()
    _, count = merge_sort_and_count(arr_copy)
    return count
