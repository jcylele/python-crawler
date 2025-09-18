import os
import re
from playwright.async_api import Page, Response, TimeoutError as PlaywrightTimeoutError

import Configs
from Ctrls import PathCtrl
from Models import ActorInfo
from Utils import LogUtil
from Workers.ImageWait.BaseWait import BaseWait


class ActorIconWait(BaseWait):
    def __init__(self):
        super().__init__(".user-header__avatar > picture > img", True)
        self.actor_info: ActorInfo | None = None
        self.actor_icon_path = ""

    def set_actor_info(self, actor_info: ActorInfo):
        self.actor_info = actor_info
        self.actor_icon_path = PathCtrl.icon_file_path(self.actor_info)
        self.set_wait(not os.path.exists(self.actor_icon_path))

    async def _on_response(self, response: Response):
        match = re.search(r"/icons/(\w+)/(\w+)$", response.url)
        if not match:
            return

        platform = match.group(1)
        actor_link = match.group(2)
        if platform != self.actor_info.actor_platform or \
                actor_link != self.actor_info.actor_link:
            return

        # stop waiting for icon
        self.set_wait(False)

        await self.save_icon(self.actor_info, response)
