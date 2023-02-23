from enum import Enum, auto

# limit the number of new actors
MaxActorsCount = 0
# limit the numbers of posts of each actor
MaxPostCount = 0
# limit the maximal size of resource(file)
MaxFileSize = 0
# left count for MaxActorsCount
__left_actor_count = -1


# connection string
DbConnectString = "mysql+pymysql://jcylele:123456@localhost:3306/onlyfans"
# Root Folder for all downloaded resources(files)
RootFolder = "D:\\OnlyFans"
# tmp file inside RootFolder for downloading files which will be  moved to other locations when completed
TmpFolder = "_downloading"


def formatTmpFolderPath() -> str:
    """
    temporary folder for downloading files
    :return:
    """
    return f"{RootFolder}\\{TmpFolder}"


def formatActorFolderPath(actor_name: str) -> str:
    """
    path of the folder for an actor
    :param actor_name:
    :return:
    """
    return f"{RootFolder}\\{actor_name}"


def setConfig(actor_count: int, post_count:int, file_size: int):
    global MaxActorsCount
    MaxActorsCount = actor_count

    global MaxPostCount
    MaxPostCount = post_count

    global MaxFileSize
    MaxFileSize = file_size

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
