import os
import re
from playwright.async_api import Response

from Utils import LogUtil
from Workers.ImageWait.BaseWait import BaseWait


class PostThumbnailWait(BaseWait):
    def __init__(self):
        super().__init__(".post__thumbnail > figure > a > img", False, True, 20000)
        self.folder_path = ""

    def set_folder_path(self, folder_path: str):
        self.folder_path = folder_path
        # create thumbnail folder(support old actor folder structure)
        os.makedirs(folder_path, exist_ok=True)

    async def _on_response(self, response: Response):
        pure_file_name = response.url.split(
            "/")[-1].split("?")[0]  # clean file name from parameters
        if not pure_file_name:  # if url ends with /
            return

        # 查找64个十六进制字符，后跟一个点，然后是文件扩展名
        # 使用 re.fullmatch 来确保整个字符串都符合模式
        # 使用 re.IGNORECASE 标志来忽略哈希值中字母的大小写
        if not re.fullmatch(r"[0-9a-f]{64}\.\w+", pure_file_name, re.IGNORECASE):
            return

        try:
            with open(f"{self.folder_path}/{pure_file_name}", "wb") as f:
                f.write(await response.body())
        except Exception as e:
            LogUtil.exception(e)
