import os
import re
from typing_extensions import override
from playwright.async_api import Response

from Ctrls import PathCtrl
from Models.ModelInfos import ActorInfo
from Workers.ImageWait.BaseIconWait import BaseIconWait


class ActorIconsWait(BaseIconWait):
    def __init__(self):
        super().__init__(".user-card__user-icon > picture > img", False, True)
        self.actor_infos: list[ActorInfo] = []

    def set_actor_infos(self, actor_infos: list[ActorInfo]):
        self.actor_infos = []
        for actor_info in actor_infos:
            icon_path = PathCtrl.icon_file_path(actor_info)
            if not os.path.exists(icon_path):
                self.actor_infos.append(actor_info)

    @override
    def get_wait(self):
        return len(self.actor_infos) > 0

    async def _on_response(self, response: Response):
        match = re.search(r"/icons/(\w+)/(\w+)$", response.url)
        if not match:
            return

        platform = match.group(1)
        actor_link = match.group(2)

        actor_index = next((i for i, x in enumerate(self.actor_infos)
                            if x.actor_platform == platform and x.actor_link == actor_link),
                           -1)  # 如果没有找到，返回 -1

        if actor_index == -1:
            return

        actor_info = self.actor_infos.pop(actor_index)

        await self.save_icon(actor_info, response)
