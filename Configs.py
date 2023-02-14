from enum import Enum, auto

# limit the number of new actors
MaxActorsCount = 0
# limit the numbers of posts of each actor
MaxPostCount = 0
# limit the maximal size of resource(file)
MaxFileSize = 0
# left count for MaxActorsCount
__left_actor_count = -1

# Root Folder for all downloaded resources(files)
RootFolder = "D:/OnlyFans"
# tmp file inside RootFolder for downloading files which will be  moved to other locations when completed
TmpFolder = "_downloading"


def formatTmpFolderPath() -> str:
    """
    temporary folder for downloading files
    :return:
    """
    return f"{RootFolder}/{TmpFolder}"


def formatActorFolderPath(actor_name: str) -> str:
    """
    path of the folder for an actor
    :param actor_name:
    :return:
    """
    return f"{RootFolder}/{actor_name}"


class ConfigType(Enum):
    """
    set of numbers
    """
    All = auto()
    Liked = auto()
    Sample = auto()


class DownConfig(object):
    """
    just to group numbers
    """

    def __init__(self, ac: int, pc: int, fs: int):
        self.MaxActorsCount = ac
        self.MaxPostCount = pc
        self.MaxFileSize = fs


# configuration set
# TODO: Use json instead
__ConfigDict: dict[ConfigType, DownConfig] = {
    ConfigType.All: DownConfig(0, 25000, 1 * 1024 * 1024 * 1024),  # 所有Post，1G以下资源
    ConfigType.Liked: DownConfig(0, 200, 200 * 1024 * 1024),  # 200条，200M
    ConfigType.Sample: DownConfig(50, 50, 50 * 1024 * 1024),  # 50条，50M
}


def setConfig(config_type: ConfigType):
    """
    set limits in batch
    """
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
    continue to enqueue new actors or not
    :param use decrease the number
    """
    global __left_actor_count
    if __left_actor_count > 0:
        if use:
            __left_actor_count -= 1
        return True
    return False
