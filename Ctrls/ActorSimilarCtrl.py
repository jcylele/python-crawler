import re
from collections.abc import Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session

from Consts import NoticeType
from Ctrls import NoticeCtrl
from Models.ActorModel import ActorModel

MIN_SUBSTRING_LEN = 12
_last_chars = ["x"]
_substring_skip = ["official", "princess"]
_substring_skip_pattern = re.compile('|'.join(re.escape(s) for s in _substring_skip))
_digit_skip = set(["u", "user"])
_pre_fix = ['the', 'free', 'goddess', 'only']
_post_fix = ["vip", "free", "official", "premium", "ppv", "clips"]
_sp_split = [".", "-", "_"]
_sp_split_pattern = f"[{re.escape(''.join(_sp_split))}]"


def _check_and_report_group(session: Session, actor_names: Iterable[str], main_actor_map: dict[str, int]):
    if not actor_names or len(actor_names) <= 1:
        return

    main_id = 0 # 0 is special
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
        if not _substring_skip_pattern.search(name)
    ]
    # group by name length
    name_length_map: dict[int, list[str]] = {}
    for name in actor_names:
        name_length = len(name)
        if name_length < MIN_SUBSTRING_LEN:
            continue
        if name_length not in name_length_map:
            name_length_map[name_length] = []
        name_length_map[name_length].append(name)

    exist_pair_map: dict[str, set[str]] = {}
    substring_map: dict[str, str] = {}
    pre_substring_map: dict[str, str] = {}
    same_substring_map: dict[str, set[str]] = {}
    max_name_length = max(name_length_map.keys())
    for name_length in range(max_name_length, MIN_SUBSTRING_LEN - 1, -1):
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
    if len(actor_name) == 0 or (actor_name in _digit_skip):
        return None

    # remove special last chars
    if actor_name[-1] in _last_chars:
        c = actor_name[-1]
        for i in range(len(actor_name) - 1, -1, -1):
            if actor_name[i] != c:
                actor_name = actor_name[:i + 1]
                break

    # keep only 1 char for duplicate last chars
    c = actor_name[-1]
    for i in range(len(actor_name) - 1, -1, -1):
        if actor_name[i] != c:
            actor_name = actor_name[:i + 2]  # keep 1 char
            break

    # remove prefix
    for prefix in _pre_fix:
        if actor_name.startswith(prefix):
            actor_name = actor_name[len(prefix):]
            break
    # remove postfix
    for postfix in _post_fix:
        if actor_name.endswith(postfix):
            actor_name = actor_name[:-len(postfix)]
            break

    if len(actor_name) == 0:
        return None

    # split by sp_chars
    cleaned_parts = [part for part in re.split(
        _sp_split_pattern, actor_name) if part]
    # sort to avoid duplicate
    if len(cleaned_parts) == 1:
        return cleaned_parts[0]
    else:
        cleaned_parts.sort()
        return "".join(cleaned_parts)

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
        main_actor_map[actor_name] = main_actor_id

    _check_similar_names_by_substring(session, main_actor_map)
    _check_similar_names_by_pure_name(session, main_actor_map)
