import json

# connection string
DbConnectString = ""
# Root Folder for all downloaded resources(files)
RootFolder = ""
# tmp file inside RootFolder for downloading files which will be  moved to other locations when completed
TmpFolder = ""
# folder for downloading icons of actors
IconFolder = ""

# minimum download speed
MIN_DOWN_SPEED = 0
# base time out for downloading files
BASE_TIME_OUT = 0
# maximum number of actors to fetch
MAX_FETCH_ACTOR_COUNT = 0
# if show Chrome browser
SHOW_BROWSER = False
# maximum score of an actor
MAX_SCORE = 12


def init():
    with open('configs/settings.json') as setting_file:
        setting_json = json.load(setting_file)
        global DbConnectString, RootFolder, TmpFolder, IconFolder, MIN_DOWN_SPEED, BASE_TIME_OUT, MAX_FETCH_ACTOR_COUNT, SHOW_BROWSER, MAX_SCORE
        DbConnectString = setting_json['DbConnectString']
        RootFolder = setting_json['RootFolder']
        TmpFolder = setting_json['TmpFolder']
        IconFolder = setting_json['IconFolder']
        MIN_DOWN_SPEED = setting_json['MIN_DOWN_SPEED']
        BASE_TIME_OUT = setting_json['BASE_TIME_OUT']
        MAX_FETCH_ACTOR_COUNT = setting_json['MAX_FETCH_ACTOR_COUNT']
        SHOW_BROWSER = setting_json['SHOW_BROWSER']
        MAX_SCORE = setting_json['MAX_SCORE']


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
