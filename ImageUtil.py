import math
import os
import re
from typing import Callable

import PIL
from PIL import Image
import Consts
import LogUtil


def traverse(root: str, recursive: bool, func: Callable[[str], None], *extra_args):
    """
    遍历文件夹，执行操作
    :param root: 根文件夹
    :param recursive: 是否遍历子文件夹
    :param func: 操作函数
    :param extra_args: 额外参数
    :return:
    """
    for fname in os.listdir(root):
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            try:
                func(path, *extra_args)
            except BaseException as e:
                LogUtil.error(f"error in traverse {path}, {e}")
            else:
                LogUtil.info(f"processed: {path}")
        elif recursive:
            traverse(path, True, func, *extra_args)

    LogUtil.info(f"{root} Done!")


def readImage(file_path: str, target_height: int = -1) -> Image:
    try:
        image = Image.open(file_path)
        if target_height != -1:
            w = math.ceil(image.width * target_height / image.height)
            image = image.resize((w, target_height), Image.Resampling.LANCZOS)
        return image
    except:
        return None


def isInvalidImage(file_path: str) -> bool:
    """
    判定不完整图片
    :param file_path: 文件路径
    :return: 不完整的图片文件返回True
    """
    try:
        Image.open(file_path).load()
        return False
    except:
        return True


def __delMergedImage(file_path: str):
    match = re.match(r'.*[/\\](\d+)\.jpg$', file_path)
    if match is None:
        return
    os.remove(file_path)
    # LogUtil.warn(file_path)

def delMergedImages():
    traverse(Consts.RootFolder, True, __delMergedImage)


def __deleteThinImages(file_path: str, min_ratio: int):
    try:
        img = Image.open(file_path)
        if ((img.width * 1000) / img.height) < min_ratio:
            img.close()
            os.remove(file_path)
    except PIL.UnidentifiedImageError:
        pass
    except BaseException as e:
        LogUtil.error(e)


def deleteThinImages(actor_name: str):
    # RecordMgr.addUser(actor_name)
    traverse(f"{Consts.RootFolder}/{actor_name}", False, __deleteThinImages, 1000)
    # RecordMgr.saveUser(actor_name)






