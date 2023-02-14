import os
from typing import Callable

import LogUtil


def traverse(root: str, recursive: bool, func: Callable[[str], None], *extra_args):
    """
    traverse through folder and process each file
    :param root: root folder
    :param recursive: traverse sub folders or not
    :param func: process function
    :param extra_args: extra arguments for the function
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
                LogUtil.debug(f"processed: {path}")
        elif recursive:
            traverse(path, True, func, *extra_args)

    LogUtil.debug(f"{root} Done!")

