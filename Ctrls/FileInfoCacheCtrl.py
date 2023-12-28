import os

import Configs
from Consts import ResState, ResType


class ResFileInfo(object):
    def __init__(self, res_state: ResState):
        self.res_state = res_state
        self.res_size = 0
        self.img_count = 0
        self.video_count = 0

    def addRes(self, res: "ResModel"):
        self.res_size += res.res_size
        if res.res_type == ResType.Image:
            self.img_count += 1
        elif res.res_type == ResType.Video:
            self.video_count += 1

    def removeRes(self, res: "ResModel"):
        self.res_size -= res.res_size
        if res.res_type == ResType.Image:
            self.img_count -= 1
        elif res.res_type == ResType.Video:
            self.video_count -= 1

    def toJson(self):
        return {
            "res_state": self.res_state.value,
            "res_size": self.res_size,
            "img_count": self.img_count,
            "video_count": self.video_count
        }


class ActorFileInfo(object):
    def __init__(self):
        self.file_info_dict: dict[ResState, ResFileInfo] = {
        }

    def addRes(self, res: "ResModel"):
        if res.res_state not in self.file_info_dict:
            self.file_info_dict[res.res_state] = ResFileInfo(res.res_state)
        self.file_info_dict[res.res_state].addRes(res)

    def onResStateChanged(self, res: "ResModel", new_state: ResState):
        # old state must exist
        old_res_file_info = self.file_info_dict.get(res.res_state)
        old_res_file_info.removeRes(res)
        # new state may not exist
        new_res_file_info = self.file_info_dict.get(new_state)
        if new_res_file_info is None:
            new_res_file_info = ResFileInfo(new_state)
            self.file_info_dict[new_state] = new_res_file_info
        new_res_file_info.addRes(res)

    def toJson(self):
        res_file_list = []
        for res_file_info in self.file_info_dict.values():
            if res_file_info.res_size == 0:
                continue
            res_file_list.append(res_file_info)
        res_file_list.sort(key=lambda x: x.res_state.value)
        return [res_file_info.toJson() for res_file_info in res_file_list]


_file_info_cache: dict[str, ActorFileInfo] = {}


def CacheFileSizes(actor_name: str, actor_file_info: ActorFileInfo):
    _file_info_cache[actor_name] = actor_file_info


def GetCachedFileSizes(actor_name: str) -> ActorFileInfo:
    if actor_name not in _file_info_cache:
        return None
    return _file_info_cache[actor_name]


def RemoveCachedFileSizes(actor_name: str):
    if actor_name in _file_info_cache:
        del _file_info_cache[actor_name]


def OnFileStateChanged(actor_name: str, res: "ResModel", new_state: ResState):
    if actor_name not in _file_info_cache:
        return
    _file_info_cache[actor_name].onResStateChanged(res, new_state)


def RemoveDownloadingFiles(actor_name: str):
    download_folder = Configs.formatTmpFolderPath()
    try:
        for root, _, files in os.walk(download_folder):
            for file in files:
                if file.startswith(f'{actor_name}_'):
                    os.remove(os.path.join(root, file))
    except Exception as e:
        pass
