import os
import re
from playwright.async_api import Response

import Configs
from Utils import LogUtil
from Workers.ImageWait.BaseWait import BaseWait


class BaseThumbnailWait(BaseWait):
    def __init__(self, selector: str, time_out: int):
        super().__init__(selector, False, True, time_out)
        self.folder_path = ""

    def set_folder_path(self, folder_path: str):
        self.folder_path = folder_path
        if not os.path.exists(self.folder_path):
            LogUtil.error(f"thumbnail folder {self.folder_path} not found")
            return
        # create thumbnail folder(support old actor folder structure)
        # os.makedirs(folder_path, exist_ok=True)

    async def _on_response(self, response: Response):
        pure_file_name = Configs.regex_thumbnail_file_name(response.url)
        if not pure_file_name:
            return

        if not os.path.exists(self.folder_path):
            return

        try:
            img_path = f"{self.folder_path}/{pure_file_name}"
            if not os.path.exists(img_path):
                with open(img_path, "wb") as f:
                    f.write(await response.body())
                LogUtil.debug(f"thumbnail {img_path} saved")
            else:
                LogUtil.debug(f"thumbnail {img_path} already exists")
        except Exception as e:
            LogUtil.exception(e)


class PostThumbnailWait(BaseThumbnailWait):
    def __init__(self):
        super().__init__(".post__thumbnail > figure > a > img", 20000)


class ActorThumbnailWait(BaseThumbnailWait):
    def __init__(self):
        super().__init__("img.post-card__image", 20000)
