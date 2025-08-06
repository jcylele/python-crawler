import json

import Configs
from Consts import CacheKey

_json_data = None
_file_path = Configs.formatStaticFile('configs/cache.json')


def init():
    global _json_data
    if _json_data is None:
        with open(_file_path, 'r') as f:
            _json_data = json.load(f)


def getValue(key: CacheKey):
    init()
    return _json_data.get(key.value, None)


def setValue(key: CacheKey, value: any):
    init()
    _json_data[key.value] = value
    with open(_file_path, 'w') as f:
        json.dump(_json_data, f)
