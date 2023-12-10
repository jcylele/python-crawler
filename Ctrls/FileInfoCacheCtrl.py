import os

import Configs

_file_info_cache = {}


def RemoveDownloadingFiles(actor_name: str):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                if file.startswith(f'{actor_name}_'):
                    os.remove(os.path.join(root, file))
    except Exception as e:
        pass


def CacheFileSizes(actor_name: str, file_sizes: dict):
    _file_info_cache[actor_name] = file_sizes


def GetCachedFileSizes(actor_name: str):
    if actor_name not in _file_info_cache:
        return None
    return _file_info_cache[actor_name]


def OnFileStateChanged(actor_name: str, old_state: int, new_state: int, file_size: int):
    if actor_name in _file_info_cache:
        size_list = _file_info_cache[actor_name]
        size_list[new_state - 1] += file_size
        size_list[old_state - 1] -= file_size


def OnActorFileChanged(actor_name: str):
    if actor_name in _file_info_cache:
        del _file_info_cache[actor_name]


def GetFileInfo(actor_name: str):
    if actor_name in _file_info_cache:
        return _file_info_cache[actor_name]
    actor_folder = Configs.formatActorFolderPath(actor_name)
    # get file count,size and type
    file_total_size = 0
    file_count_map = {}

    if not os.path.exists(actor_folder):
        info = {}
        _file_info_cache[actor_name] = info
        return info

    for root, _, files in os.walk(actor_folder):
        for file in files:
            file_total_size += os.path.getsize(os.path.join(root, file))
            ext = os.path.splitext(file)[1]
            if ext not in file_count_map:
                file_count_map[ext] = 0
            file_count_map[ext] += 1

    info = {
        'size': file_total_size,
        'count': file_count_map
    }

    _file_info_cache[actor_name] = info

    return info
