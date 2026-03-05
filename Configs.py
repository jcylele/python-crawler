import os
import re
import sys

from Consts import CacheFile, CacheKey, QueueType, WorkerType
from Utils import CacheUtil, PathUtil

# folder inside RootFolder for downloading files which will be  moved to other locations when completed
DownloadingFolder = "_downloading"
# folder for downloading icons of actors
IconFolder = "_icon"
# folder for temporary files
TmpFolder = "_tmp"
# web path for files, app mount prefix
FileWebPath = "files"

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
# database fields length
DB_BYTES_LEN_SHA256 = 32
DB_STR_LEN_COLOR = 7
DB_STR_LEN_EXTENSION = 10
DB_STR_LEN_BIG_INT = 20
DB_STR_LEN_SHORT = 30
DB_STR_LEN_MD5 = 32
DB_STR_LEN_DOMAIN = 50
DB_STR_LEN_LONG = 100
DB_STR_LEN_REMARK = 200
# length of dm post is 2 + N * this length
DM_LEN_SINGLE_ID = 18


def getSetting(cache_key: CacheKey):
    return CacheUtil.getValue(CacheFile.Settings, cache_key)


def setSetting(cache_key: CacheKey, value: any):
    CacheUtil.setValue(CacheFile.Settings, cache_key, value)


def getRootFolder() -> str:
    return getSetting(CacheKey.RootFolder)


def getWaitAllImagesJs(selector: str) -> str:
    global WAIT_ALL_IMAGES_JS
    if WAIT_ALL_IMAGES_JS is None:
        with open(PathUtil.formatStaticFile('configs/wait_all_images.js'), 'r', encoding='utf-8') as wait_for_images_js_file:
            WAIT_ALL_IMAGES_JS = wait_for_images_js_file.read()
    return f"({WAIT_ALL_IMAGES_JS})('{selector}')"


def getWaitSingleImageJs(selector: str) -> str:
    global WAIT_SINGLE_IMAGE_JS
    if WAIT_SINGLE_IMAGE_JS is None:
        with open(PathUtil.formatStaticFile('configs/wait_single_image.js'), 'r', encoding='utf-8') as wait_for_images_js_file:
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

def formatTmpFolderPath() -> str:
    return f"{getRootFolder()}\\{TmpFolder}"

def formatDownloadingFolderPath() -> str:
    """
    temporary folder for downloading files
    :return:
    """
    return f"{getRootFolder()}\\{DownloadingFolder}"


def formatIconFolderPath() -> str:
    """
    folder for downloading icons of actors
    :return:
    """
    return f"{getRootFolder()}\\{IconFolder}"


def formatActorFolderPath(actor_id: int, actor_name: str) -> str:
    return f"{getRootFolder()}\\{actor_name}_{actor_id}"


def formatActorThumbnailFolderPath(actor_id: int, actor_name: str) -> str:
    return f"{formatActorFolderPath(actor_id, actor_name)}\\{formatThumbnailFolderName(actor_name)}"


def formatThumbnailFolderName(actor_name: str) -> str:
    return f"_{actor_name}"


def regex_thumbnail_file_name(url: str) -> str | None:
    # clean file name from parameters
    pure_file_name = url.split("/")[-1].split("?")[0]
    if not pure_file_name:
        return None

    # 查找64个十六进制字符，后跟一个点，然后是文件扩展名
    # 使用 re.fullmatch 来确保整个字符串都符合模式
    # 使用 re.IGNORECASE 标志来忽略哈希值中字母的大小写
    if not re.fullmatch(r"[0-9a-f]{64}\.\w+", pure_file_name, re.IGNORECASE):
        return None

    return pure_file_name


def regex_actor_icon_file_name(url: str) -> tuple[str, str] | tuple[None, None]:
    match = re.search(r"/icons/(\w+)/([\w\-\.]+)$", url)
    if not match:
        return (None, None)

    platform = match.group(1)
    actor_link = match.group(2)
    return (platform, actor_link)


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
