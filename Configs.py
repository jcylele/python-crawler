import json
import os
import sys
from os import path

from Consts import QueueType, WorkerType

# connection string
DbConnectString = ""
# root url from where to download
RootUrl = ""
IconUrl = ""
ServerPort = 7878
# Root Folder for all downloaded resources(files)
RootFolder = ""
# tmp file inside RootFolder for downloading files which will be  moved to other locations when completed
TmpFolder = "_downloading"
# folder for downloading icons of actors
IconFolder = "_icon"
# web path for files, app mount prefix
FileWebPath = "files"
# thumbnail image folder in actor folder
ThumbnailFolder = "_thumbnail"

# minimum download speed
MIN_DOWN_SPEED = 0
# base time out for downloading files
BASE_TIME_OUT = 0
# if show Chrome browser
SHOW_BROWSER = False

# wait for images js
WAIT_ALL_IMAGES_JS: str | None = None
WAIT_SINGLE_IMAGE_JS: str | None = None

### above variables are in configs/settings.json, below are constants ###

# maximum score of an actor
MAX_SCORE = 12
# res between RES_SIZE_LIST[i-1] and RES_SIZE_LIST[i] will be put into RES_SIZE_LIST[i] segment
RES_SIZE_LIST = []
MIN_RES_SIZE = 4 * 1024 * 1024
MAX_RES_SIZE = 1024 * 1024 * 1024

# port for file server, only icons now
FILE_PORT = 1314

DB_BYTES_LEN_SHA256 = 32

DB_STR_LEN_COLOR = 7
DB_STR_LEN_EXTENSION = 10
DB_STR_LEN_BIG_INT = 20
DB_STR_LEN_SHORT = 30
DB_STR_LEN_MD5 = 32
DB_STR_LEN_DOMAIN = 50
DB_STR_LEN_LONG = 100
DB_STR_LEN_REMARK = 200


def init():
    with open(formatStaticFile('configs/settings.json'), 'r') as setting_file:
        setting_json = json.load(setting_file)
        global DbConnectString, RootUrl, IconUrl, ServerPort, RootFolder, MIN_DOWN_SPEED, BASE_TIME_OUT, SHOW_BROWSER
        DbConnectString = setting_json['DbConnectString']
        RootUrl = setting_json['RootUrl']
        IconUrl = setting_json['IconUrl']
        ServerPort = setting_json['ServerPort']
        RootFolder = setting_json['RootFolder']
        MIN_DOWN_SPEED = setting_json['MIN_DOWN_SPEED']
        BASE_TIME_OUT = setting_json['BASE_TIME_OUT']
        SHOW_BROWSER = setting_json['SHOW_BROWSER']


def getWaitAllImagesJs(selector: str) -> str:
    global WAIT_ALL_IMAGES_JS
    if WAIT_ALL_IMAGES_JS is None:
        with open(formatStaticFile('configs/wait_all_images.js'), 'r', encoding='utf-8') as wait_for_images_js_file:
            WAIT_ALL_IMAGES_JS = wait_for_images_js_file.read()
    return f"({WAIT_ALL_IMAGES_JS})('{selector}')"


def getWaitSingleImageJs(selector: str) -> str:
    global WAIT_SINGLE_IMAGE_JS
    if WAIT_SINGLE_IMAGE_JS is None:
        with open(formatStaticFile('configs/wait_single_image.js'), 'r', encoding='utf-8') as wait_for_images_js_file:
            WAIT_SINGLE_IMAGE_JS = wait_for_images_js_file.read()
    return f"({WAIT_SINGLE_IMAGE_JS})('{selector}')"


def __generateResSizeList() -> list[int]:
    ret = [0]
    res_size = MIN_RES_SIZE
    while res_size <= MAX_RES_SIZE:
        ret.append(res_size)
        res_size *= 2
    return ret


def getResSizeList() -> list[int]:
    global RES_SIZE_LIST
    if len(RES_SIZE_LIST) == 0:
        RES_SIZE_LIST = __generateResSizeList()
    return RES_SIZE_LIST


def initPlaywright():
    # Check if the application is running as a frozen executable (packaged by PyInstaller)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # The '0' value seems unreliable in some bundled environments.
        # Instead, we construct the full, absolute path to the system-wide
        # Playwright browser installation directory and set that.

        local_app_data = os.getenv('LOCALAPPDATA')
        if local_app_data:
            browsers_path = os.path.join(local_app_data, 'ms-playwright')
            print(
                f"PyInstaller mode detected. Setting Playwright browsers path to: {browsers_path}")
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
        else:
            # Fallback or error if LOCALAPPDATA is not set
            print(
                "Warning: LOCALAPPDATA environment variable not found. Playwright might fail.")


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


def formatActorFolderPath(actor_id: int, actor_name: str) -> str:
    return f"{RootFolder}\\{actor_name}_{actor_id}"


def formatActorThumbnailFolderPath(actor_id: int, actor_name: str) -> str:
    return f"{formatActorFolderPath(actor_id, actor_name)}\\_{actor_name}"


def getQueueTypeByWorkerType(worker_type: WorkerType) -> QueueType:
    match worker_type:
        case WorkerType.FileDown:
            return QueueType.FileDownload
        case WorkerType.ResInfo:
            return QueueType.ResInfo
        case WorkerType.ResValid:
            return QueueType.ResValid
        case WorkerType.FetchActors:
            return QueueType.FetchActors
        case WorkerType.FetchActor:
            return QueueType.FetchActor
        case WorkerType.FetchActorLink:
            return QueueType.FetchActorLink
        case WorkerType.FetchPost:
            return QueueType.FetchPost
        case _:
            raise ValueError(f"Invalid worker type: {worker_type}")
