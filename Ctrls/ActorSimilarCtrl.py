import asyncio
from dataclasses import dataclass
import os
import re
from collections.abc import Callable, Iterable
from typing import Pattern, TypedDict
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from Consts import CacheFile, CacheKey, NoticeType
from Ctrls import ImageHashCtrl, NoticeCtrl, PathCtrl
from Models.ActorModel import ActorModel
from Models.ModelInfos import ActorInfo
from Utils import CacheUtil, LogUtil
from Utils.PyUtil import time_cost
from routers.schemas_others import ActorNameStatsData, ActorNameStatsNode


@dataclass
class SimilarConfigs:
    similar_icon_threshold: int
    min_substring_len: int
    min_pure_name_len: int
    substring_skip_pattern: Pattern
    prefix_pattern: Pattern
    postfix_pattern: Pattern
    sp_split_pattern: Pattern
    sp_last_pattern: Pattern


_similar_configs: SimilarConfigs | None = None


def _init_similar_configs():
    global _similar_configs
    if _similar_configs is not None:
        return
    json = CacheUtil.getJson(CacheFile.SimilarConfigs)
    _similar_configs = SimilarConfigs(
        similar_icon_threshold=json.get(
            CacheKey.SimilarIconThreshold.value),
        min_substring_len=json.get(
            CacheKey.SimilarMinSubstringLen.value),
        min_pure_name_len=json.get(
            CacheKey.SimilarMinPureNameLen.value),
        substring_skip_pattern=re.compile(
            '|'.join(re.escape(s)
                     for s in json.get(CacheKey.SimilarNameSubstringSkip.value)),
            re.IGNORECASE
        ),
        prefix_pattern=re.compile(
            r'^(' + '|'.join(re.escape(p)
                             for p in json.get(CacheKey.SimilarNamePreFix.value)) + ')',
            re.IGNORECASE
        ),
        postfix_pattern=re.compile(
            r'('
            + '|'.join(re.escape(p)
                       for p in json.get(CacheKey.SimilarNamePostFix.value))
            + ')$',
            re.IGNORECASE
        ),
        sp_split_pattern=re.compile(
            f"[{re.escape(''.join(json.get(CacheKey.SimilarSpSplitChars.value)))}]",
            re.IGNORECASE
        ),
        sp_last_pattern=re.compile(
            r'(?:'
            + '|'.join(re.escape(p)
                       for p in json.get(CacheKey.SimilarSpLastChars.value))
            + ')+$',
            re.IGNORECASE
        )
    )
# region name similar


def _check_and_report_group(session: Session, actor_names: Iterable[str], main_actor_map: dict[str, int]):
    if not actor_names or len(actor_names) <= 1:
        return

    main_id = 0  # 0 is special
    for name in actor_names:
        id = main_actor_map.get(name)
        if main_id == 0:
            main_id = id
        elif id != main_id:
            NoticeCtrl.addNoticeStrict(
                session, NoticeType.SimilarActorName, actor_names)
            return


def _check_similar_names_by_substring(session: Session, main_actor_map: dict[str, int]):
    """
    通过类似滚动窗口的方式，检查具有公共子串的pairs
    每一轮检查，字符串s分裂为s[:-1], s[1:]并进行相等判定
    """
    actor_names = [
        name for name in main_actor_map.keys()
        if not _similar_configs.substring_skip_pattern.search(name)
    ]
    # group by name length
    name_length_map: dict[int, list[str]] = {}
    for name in actor_names:
        name_length = len(name)
        if name_length < _similar_configs.min_substring_len:
            continue
        if name_length not in name_length_map:
            name_length_map[name_length] = []
        name_length_map[name_length].append(name)

    exist_pair_map: dict[str, set[str]] = {}
    substring_map: dict[str, str] = {}
    pre_substring_map: dict[str, str] = {}
    same_substring_map: dict[str, set[str]] = {}
    max_name_length = max(name_length_map.keys())
    for name_length in range(max_name_length, _similar_configs.min_substring_len - 1, -1):
        # first, put names of this length into substring_map, no conflict
        names = name_length_map.get(name_length)
        if names is None:
            continue
        for name in names:
            substring_map[name] = name
        # split pre_substring_map
        for substring, full_name in pre_substring_map.items():
            for new_sub in [substring[:-1], substring[1:]]:
                exist_name = substring_map.get(new_sub)
                if exist_name is None:
                    substring_map[new_sub] = full_name
                elif exist_name == full_name:
                    pass
                else:
                    same_set = same_substring_map.get(new_sub)
                    if same_set is None:
                        same_set = set()
                        same_set.add(exist_name)
                        same_set.add(full_name)
                        same_substring_map[new_sub] = same_set
                    else:
                        same_set.add(full_name)
        # check and report same_substring_map
        for substring, same_set in same_substring_map.items():
            # remove from substring_map, reduce duplicate check
            substring_map.pop(substring)
            # check and skip existed pair, larger set not supported yet
            min_name = min(same_set)
            exist_pair_set = exist_pair_map.get(min_name)
            if exist_pair_set is None:
                exist_pair_map[min_name] = same_set  # reuse same_set safely
            else:
                if same_set.issubset(exist_pair_set):
                    continue
                else:
                    exist_pair_map[min_name] = exist_pair_set.union(same_set)
            _check_and_report_group(session, same_set, main_actor_map)
            # print(f"same substring: {substring}, {same_set}")

        # swap and cleanup
        substring_map, pre_substring_map = pre_substring_map, substring_map
        substring_map.clear()
        same_substring_map.clear()


def _possible_pure_name(actor_name: str) -> str | None:
    # remove last digits
    for i in range(len(actor_name) - 1, -1, -1):
        if not actor_name[i].isdigit():
            actor_name = actor_name[:i + 1]
            break

    # pure digit skip
    if len(actor_name) < _similar_configs.min_pure_name_len:
        return None

    # remove consecutive special last chars
    actor_name = _similar_configs.sp_last_pattern.sub('', actor_name)

    if len(actor_name) < _similar_configs.min_pure_name_len:
        return None

    # keep only 1 char for duplicate last chars
    # substring will find them
    # c = actor_name[-1]
    # for i in range(len(actor_name) - 1, -1, -1):
    #     if actor_name[i] != c:
    #         actor_name = actor_name[:i + 2]  # keep 1 char
    #         break

    # remove prefix
    changed = True
    while changed:
        changed = False
        match = _similar_configs.prefix_pattern.match(actor_name)
        if match:
            matched_prefix = match.group(1)
            actor_name = actor_name[len(matched_prefix):]
            changed = True

    # remove postfix
    changed = True
    while changed:
        changed = False
        match = _similar_configs.postfix_pattern.search(actor_name)
        if match:
            matched_postfix = match.group(1)
            actor_name = actor_name[:-len(matched_postfix)]
            changed = True

    if len(actor_name) < _similar_configs.min_pure_name_len:
        return None

    # split by sp_chars
    cleaned_parts = [part for part in
                     _similar_configs.sp_split_pattern.split(actor_name)
                     if part]
    # sort to avoid duplicate
    pure_name = ""
    if len(cleaned_parts) == 1:
        pure_name = cleaned_parts[0]
    else:
        cleaned_parts.sort()
        pure_name = "".join(cleaned_parts)

    if len(pure_name) < _similar_configs.min_pure_name_len:
        return None

    return pure_name


def _check_similar_names_by_pure_name(session: Session, main_actor_map: dict[str, int]):
    """
    通过去除常见前后缀，特殊符号和其他规则，得到“词根”，并检查具有相同词根的pairs
    """
    pure_name_map: dict[str, list[str]] = {}
    for actor_name in main_actor_map.keys():
        pure_name = _possible_pure_name(actor_name)
        if pure_name is None:
            continue
        if pure_name in pure_name_map:
            pure_name_map[pure_name].append(actor_name)
        else:
            pure_name_map[pure_name] = [actor_name]

    for pure_name, actor_names in pure_name_map.items():
        if len(actor_names) > 1:
            _check_and_report_group(session, actor_names, main_actor_map)


def check_similar_names(session: Session):
    main_actor_map: dict[str, int] = {}

    stmt = (
        select(ActorModel.actor_name, ActorModel.main_actor_id)
    )
    result = session.execute(stmt)

    for row in result:
        actor_name, main_actor_id = row
        main_actor_map[str.lower(actor_name)] = main_actor_id
    _init_similar_configs()
    _check_similar_names_by_substring(session, main_actor_map)
    _check_similar_names_by_pure_name(session, main_actor_map)

# endregion name similar

# region icon similar


def _batch_update_icon_hash(session: Session, updates: list[tuple[int, str]]):
    """批量更新icon_hash"""
    mappings = [
        {'actor_id': actor_id, 'icon_hash': hash_value}
        for actor_id, hash_value in updates
    ]
    session.bulk_update_mappings(ActorModel, mappings)
    session.flush()


@time_cost
def _fullfill_icon_hash(session: Session):
    """
    填充icon_hash字段
    """
    # 只读取必要字段，减少内存占用
    stmt = select(
        ActorModel.actor_id,
        ActorModel.actor_name,
        ActorModel.actor_platform
    ).where(ActorModel.icon_hash.is_(None))

    result = session.execute(stmt).all()
    BATCH_SIZE = 100  # 每批处理100个

    updates: list[tuple[int, str]] = []
    actor_info = ActorInfo()
    for row in result:
        actor_id, actor_name, actor_platform = row
        # 构建 ActorInfo 来获取 icon_path
        actor_info.actor_name = actor_name
        actor_info.actor_platform = actor_platform
        icon_path = PathCtrl.icon_file_path(actor_info)

        # 检查文件是否存在
        if not os.path.exists(icon_path):
            continue

        try:
            hash_value = ImageHashCtrl.phash(icon_path)
            updates.append((actor_id, str(hash_value)))
        except Exception as e:
            LogUtil.warning(f"Failed to calculate hash for {icon_path}: {e}")
            continue

        # 批量更新
        if len(updates) >= BATCH_SIZE:
            _batch_update_icon_hash(session, updates)
            updates = []

    # 处理剩余的
    if updates:
        _batch_update_icon_hash(session, updates)


def _are_names_similar(icon_names: list[str]) -> bool:
    # skip if all actor names are same
    same_actor_name = None
    for actor_name in icon_names:
        if same_actor_name is None:
            same_actor_name = actor_name
        elif same_actor_name != actor_name:
            same_actor_name = None
            break
    if same_actor_name is not None:
        return True

    # skip if all actor names are similiar
    same_pure_name = None
    for actor_name in icon_names:
        pure_name = _possible_pure_name(actor_name)
        if pure_name is None:
            same_pure_name = None
            break
        if same_pure_name is None:
            same_pure_name = pure_name
        elif same_pure_name != pure_name:
            same_pure_name = None
            break
    if same_pure_name is not None:
        return True

    return False


def _add_similar_icon_notice(session: Session, actor_names: list[str]):
    if _are_names_similar(actor_names):
        return
    NoticeCtrl.addNoticeStrict(session, NoticeType.SimilarIcon, actor_names)


async def _check_similar_icons(session: Session):
    icon_hashes = _get_all_icon_hashes(session)
    for i in range(len(icon_hashes)):
        tup_i = icon_hashes[i]
        if tup_i[2]:
            continue
        for j in range(i):
            tup_j = icon_hashes[j]
            if tup_i[3] == tup_j[3]:
                continue
            delta = _hamming_distance_early_exit(
                tup_i[1], tup_j[1], _similar_configs.similar_icon_threshold)
            if delta is not None:
                _add_similar_icon_notice(session, [tup_i[0], tup_j[0]])
        # 避免卡死
        await asyncio.sleep(0)


def _set_icon_hash_compared(session: Session):
    stmt = (update(ActorModel)
            .where(ActorModel.icon_hash_compared.is_(False))
            .where(ActorModel.icon_hash.isnot(None))
            .values(icon_hash_compared=True))
    session.execute(stmt)
    session.flush()


@time_cost
async def check_similar_icons(session: Session):
    _init_similar_configs()
    _fullfill_icon_hash(session)
    await _check_similar_icons(session)
    _set_icon_hash_compared(session)


def _get_all_icon_hashes(session: Session) -> list[tuple[str, int, bool, int]]:
    """
    获取所有icon_hash不为空的actor，并按icon_hash_compared=true在前排序
    返回值为[(actor_name, icon_hash, icon_hash_compared, main_actor_id)]
    """
    stmt = (select(ActorModel.actor_name, ActorModel.icon_hash, ActorModel.icon_hash_compared, ActorModel.main_actor_id)
            .where(ActorModel.icon_hash.isnot(None))
            .order_by(ActorModel.icon_hash_compared.desc()))
    result = session.execute(stmt)
    tup_list: list[tuple[str, int, bool, int]] = []
    for row in result:
        actor_name, actor_hash, icon_hash_compared, main_actor_id = row
        tup_list.append((actor_name, int(actor_hash, 16),
                        icon_hash_compared, main_actor_id))
    return tup_list


def _hamming_distance_early_exit(int1: int, int2: int, threshold=64) -> int | None:
    """
    计算两个整数的汉明距离（二进制表示中不同的位数）
    如果超过max_diff则提前返回None
    """
    xor = int1 ^ int2
    diff_count = 0

    # 使用位运算逐位检查
    while xor > 0:
        if xor & 1:
            diff_count += 1
            if diff_count > threshold:
                return None  # 超过阈值，提前返回
        xor >>= 1

    return diff_count

# endregion icon similar

# region name pattern stats


def _sub_prefix(s: str, len: int) -> str:
    return s[:len]


def _sub_postfix(s: str, len: int) -> str:
    return s[-len:]


def _get_name_pattern_stats(session: Session, min_len: int, max_len: int, limit: int, sub_func: Callable[[str, int], str]) -> ActorNameStatsNode:
    stmt = select(ActorModel.actor_name)
    result = session.scalars(stmt).all()
    segment_arr: list[dict[str, int]] = []
    for i in range(max_len + 1):
        segment_arr.append({})

    for row in result:
        actor_name = str.lower(row)
        for i in range(min_len, max_len + 1):
            segment = sub_func(actor_name, i)
            if segment in segment_arr[i]:
                segment_arr[i][segment] += 1
            else:
                segment_arr[i][segment] = 1

    last_stats_dict: dict[str, ActorNameStatsNode] = {}
    cur_stats_dict: dict[str, ActorNameStatsNode] = {}
    for i in range(max_len, min_len-1, -1):
        dict_i = segment_arr[i]
        sorted_dict = sorted(dict_i.items(), key=lambda x: x[1], reverse=True)
        # top prefix of the level
        for rank, (segment, count) in enumerate(sorted_dict[:limit]):
            node = ActorNameStatsNode(
                segment=segment, count=count, rank=rank+1, children=[])
            cur_stats_dict[segment] = node
        # link children to this level
        for child_node in last_stats_dict.values():
            segment = sub_func(child_node.segment, i)
            if segment in cur_stats_dict:
                node = cur_stats_dict[segment]
            else:  # not in top tier, but ascending of a top tier
                node = ActorNameStatsNode(
                    segment=segment, count=dict_i[segment], rank=0, children=[])
                cur_stats_dict[segment] = node
            node.children.append(child_node)
        # sort children by count
        for node in cur_stats_dict.values():
            node.children.sort(key=lambda x: x.count, reverse=True)
        # swap
        last_stats_dict = cur_stats_dict
        cur_stats_dict = {}
    # fake root node
    root_node = ActorNameStatsNode(
        segment="", count=0, rank=0, children=[])
    for child_node in last_stats_dict.values():
        root_node.children.append(child_node)
    root_node.children.sort(key=lambda x: x.count, reverse=True)

    return root_node


def get_name_prefix_stats(session: Session, min_len: int, max_len: int, limit: int) -> ActorNameStatsNode:
    return _get_name_pattern_stats(session, min_len, max_len, limit, _sub_prefix)


def get_name_postfix_stats(session: Session, min_len: int, max_len: int, limit: int) -> ActorNameStatsNode:
    return _get_name_pattern_stats(session, min_len, max_len, limit, _sub_postfix)


def get_common_substring_stats(session: Session, min_len: int, max_len: int, limit: int) -> list[list[ActorNameStatsData]]:
    stmt = select(ActorModel.actor_name)
    result = session.scalars(stmt).all()
    substring_arr: list[dict[str, int]] = []
    for l in range(max_len + 1):
        substring_arr.append({})

    for row in result:
        actor_name = str.lower(row)
        for l in range(min_len, max_len + 1):
            # 如果子串长度大于字符串长度，跳过
            if l > len(actor_name):
                continue
            ss_dict: dict[str, int] = substring_arr[l]
            for j in range(len(actor_name) - l + 1):
                segment = actor_name[j:j+l]
                if segment in ss_dict:
                    ss_dict[segment] += 1
                else:
                    ss_dict[segment] = 1

    result: list[list[ActorNameStatsData]] = []
    for l in range(min_len, max_len + 1):
        ss_data_list: list[ActorNameStatsData] = []
        sorted_dict = sorted(
            substring_arr[l].items(), key=lambda x: x[1], reverse=True)
        for segment, count in sorted_dict[:limit]:
            data = ActorNameStatsData(segment=segment, count=count)
            ss_data_list.append(data)
        ss_data_list.sort(key=lambda x: x.count, reverse=True)
        result.append(ss_data_list)
    return result


# endregion name pattern stats
