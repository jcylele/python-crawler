
# connection string
DbConnectString = "mysql+pymysql://jcylele:123456@localhost:3306/onlyfans"
# Root Folder for all downloaded resources(files)
RootFolder = "D:\\OnlyFans"
# tmp file inside RootFolder for downloading files which will be  moved to other locations when completed
TmpFolder = "_downloading"
IconFolder = "_icon"


def formatTmpFolderPath() -> str:
    """
    temporary folder for downloading files
    :return:
    """
    return f"{RootFolder}\\{TmpFolder}"


def formatIconFolderPath() -> str:
    """
    folder for downloading icons of actors
    :return:
    """
    return f"{RootFolder}\\{IconFolder}"


def formatActorFolderPath(actor_name: str) -> str:
    """
    path of the folder for an actor
    :param actor_name:
    :return:
    """
    return f"{RootFolder}\\{actor_name}"
