import os
from playwright.async_api import Response
from Ctrls import PathCtrl
from Models.ModelInfos import ActorInfo
from Utils import LogUtil
from Workers.ImageWait.BaseWait import BaseWait


class BaseIconWait(BaseWait):
    def __init__(self, selector: str, is_single: bool, need_scroll: bool = False, time_out: int = 10000):
        super().__init__(selector, is_single, need_scroll, time_out)

    async def save_icon(self, actor_info: ActorInfo, response: Response):
        try:
            icon_path = PathCtrl.icon_file_path(actor_info)
            if not os.path.exists(icon_path):
                with open(icon_path, "wb") as f:
                    f.write(await response.body())
                LogUtil.info(f"icon {icon_path} saved")
            else:
                LogUtil.info(f"icon {icon_path} already exists")
        except Exception as e:
            LogUtil.exception(e)
