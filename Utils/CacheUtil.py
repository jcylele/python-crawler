"""
json文件管理，默认情况单层kv的json，不支持多层嵌套，不支持新增key
"""
import json

from Consts import CacheFile, CacheKey, DateFormat
from Utils import PyUtil

_json_map: dict[CacheFile, dict[str, any]] = {}


def filePath(cache_file: CacheFile):
    return PyUtil.formatStaticFile(cache_file.value)


def init(cache_file: CacheFile):
    if cache_file in _json_map:
        return
    with open(filePath(cache_file), 'r') as f:
        _json_map[cache_file] = json.load(f)


def getValue(cache_file: CacheFile, key: CacheKey):
    init(cache_file)
    return _json_map[cache_file].get(key.value, None)


def setValue(cache_file: CacheFile, key: CacheKey, value: any, save: bool = True):
    init(cache_file)
    _file = _json_map[cache_file]
    # 默认不允许设置不存在的key
    if key.value not in _file:
        return
    _file[key.value] = value
    if save:
        saveFile(cache_file)


def saveFile(cache_file: CacheFile):
    if cache_file not in _json_map:
        return
    with open(filePath(cache_file), 'w') as f:
        json.dump(_json_map[cache_file], f, indent=4, sort_keys=True)


def getJson(cache_file: CacheFile) -> dict[str, any]:
    init(cache_file)
    return _json_map[cache_file]


def setCustomPage(page: int):
    setValue(CacheFile.CustomPage, CacheKey.CustomPage, page)


def getCustomPage() -> int:
    return getValue(CacheFile.CustomPage, CacheKey.CustomPage)


def getSettings() -> dict[str, any]:
    return getJson(CacheFile.Settings)


def changeSetting(setting_name: CacheKey, setting_value: any):
    setValue(CacheFile.Settings, setting_name, setting_value)

# 新增：获取上次运行时间的字典


def getLastRunTimes() -> dict[str, str]:
    return getJson(CacheFile.LastRunTime)


# 新增：尝试更新上次运行时间
def tryUpdateLastRunTime(api_path: str):
    last_run_times = getLastRunTimes()

    if api_path in last_run_times:
        last_run_times[api_path] = PyUtil.format_now(DateFormat.Full)
        saveFile(CacheFile.LastRunTime)
