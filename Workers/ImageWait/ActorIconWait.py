import os
import re
from playwright.async_api import Response

import Configs
from Ctrls import PathCtrl
from Models.ModelInfos import ActorInfo
from Utils import LogUtil
from Workers.ImageWait.BaseIconWait import BaseIconWait


class ActorIconWait(BaseIconWait):
    def __init__(self):
        super().__init__(".user-header__avatar > picture > img", True)
        self.actor_info: ActorInfo | None = None
        self.actor_icon_path = ""

    def set_actor_info(self, actor_info: ActorInfo):
        self.actor_info = actor_info
        self.actor_icon_path = PathCtrl.icon_file_path(self.actor_info)
        self.set_wait(not os.path.exists(self.actor_icon_path))

    async def _on_response(self, response: Response):
        platform, actor_link = Configs.regex_actor_icon_file_name(response.url)

        if platform is None or actor_link is None:
            return
        if platform != self.actor_info.actor_platform \
                or actor_link != self.actor_info.actor_link:
            LogUtil.warning(
                f"actor icon {response.url} not match {self.actor_info}")
            return

        # stop waiting for icon
        self.set_wait(False)

        await self.save_icon(self.actor_info, response)
