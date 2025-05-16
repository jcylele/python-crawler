import json
import os
import sys
from os import path

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
# if show Chrome browser
SHOW_BROWSER = False

### above variables are in configs/settings.json, below are constants ###

# maximum score of an actor
MAX_SCORE = 12
# res between RES_SIZE_LIST[i-1] and RES_SIZE_LIST[i] will be put into RES_SIZE_LIST[i] segment
RES_SIZE_LIST = [0, 16 * 1024 * 1024, 32 * 1024 * 1024, 64 * 1024 * 1024,
                 128 * 1024 * 1024, 256 * 1024 * 1024, 512 * 1024 * 1024, 1024 * 1024 * 1024]
# port for file server, only icons now
FILE_PORT = 1314


DB_BYTES_LEN_SHA256 = 32

DB_STR_LEN_COLOR = 7
DB_STR_LEN_EXTENSION = 10
DB_STR_LEN_SHORT = 30
DB_STR_LEN_MD5 = 32
DB_STR_LEN_DOMAIN = 50
DB_STR_LEN_LONG = 100
DB_STR_LEN_REMARK = 200


def init():
    with open(formatStaticFile('configs/settings.json')) as setting_file:
        setting_json = json.load(setting_file)
        global DbConnectString, RootFolder, TmpFolder, IconFolder, MIN_DOWN_SPEED, BASE_TIME_OUT, SHOW_BROWSER
        DbConnectString = setting_json['DbConnectString']
        RootFolder = setting_json['RootFolder']
        TmpFolder = setting_json['TmpFolder']
        IconFolder = setting_json['IconFolder']
        MIN_DOWN_SPEED = setting_json['MIN_DOWN_SPEED']
        BASE_TIME_OUT = setting_json['BASE_TIME_OUT']
        SHOW_BROWSER = setting_json['SHOW_BROWSER']


def formatStaticFile(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        bundle_dir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # print(bundle_dir)
    return path.join(bundle_dir, relative_path)


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


def formatIconFolderUrl() -> str:
    return f"http://localhost:{FILE_PORT}/{IconFolder}"


def formatActorFolderPath(actor_id: int, actor_name: str) -> str:
    return f"{RootFolder}\\{actor_name}_{actor_id}"
