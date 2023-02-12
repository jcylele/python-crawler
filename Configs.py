from enum import Enum

# 拉多少个新Actor
MaxActorsCount = 0
# 每个Actor拉取多少个Post
MaxPostCount = 0
# 文件大小限制
MaxFileSize = 0
# 剩余可拉Actor数量
__left_actor_count = -1


class ConfigType(Enum):
    All = 1
    Liked = 2
    Sample = 3


class DownConfig(object):
    def __init__(self, ac: int, pc: int, fs: int):
        self.MaxActorsCount = ac
        self.MaxPostCount = pc
        self.MaxFileSize = fs


__ConfigDict: dict[ConfigType, DownConfig] = {
    ConfigType.All: DownConfig(0, 25000, 1 * 1024 * 1024 * 1024),  # 所有Post，1G以下资源
    ConfigType.Liked: DownConfig(0, 200, 200 * 1024 * 1024),  # 200条，200M
    ConfigType.Sample: DownConfig(50, 50, 50 * 1024 * 1024),  # 50条，50M
}


def setConfig(config_type: ConfigType):
    config = __ConfigDict.get(config_type)
    if config is None:
        raise Exception(f"invalid Config Type: {config_type}")

    global MaxActorsCount
    MaxActorsCount = config.MaxActorsCount

    global MaxPostCount
    MaxPostCount = config.MaxPostCount

    global MaxFileSize
    MaxFileSize = config.MaxFileSize

    global __left_actor_count
    __left_actor_count = MaxActorsCount


def moreActor(use: bool) -> bool:
    """
    还可以拉么
    """
    global __left_actor_count
    if __left_actor_count > 0:
        if use:
            __left_actor_count -= 1
        return True
    return False
