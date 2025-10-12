import os
from playwright.async_api import Page, Response, TimeoutError as PlaywrightTimeoutError

import Configs
from Ctrls import PathCtrl
from Models.ActorInfo import ActorInfo
from Utils import LogUtil


class BaseWait:
    def __init__(self, selector: str, is_single: bool, need_scroll: bool = False, time_out: int = 10000):
        self._wait_img = False
        self.need_scroll = need_scroll
        self.time_out = time_out
        if is_single:
            self.js_func = Configs.getWaitSingleImageJs(selector)
        else:
            self.js_func = Configs.getWaitAllImagesJs(selector)

    def get_class_name(self):
        return self.__class__.__name__
        
    def set_wait(self, is_wait: bool):
        self._wait_img = is_wait

    def get_wait(self):
        return self._wait_img

    async def wait(self, page: Page):
        if not self.get_wait():
            LogUtil.info(f"wait {self.get_class_name()} is not wait")
            return
        try:
            if self.need_scroll:
                await self.scroll_to_bottom(page)
            await page.wait_for_function(self.js_func, timeout=self.time_out)
            LogUtil.info(f"wait {self.get_class_name()} finished")
        except PlaywrightTimeoutError:
            LogUtil.warning(f"wait {self.get_class_name()} timeout")

    async def _on_response(self, response: Response):
        raise NotImplementedError(
            "subclasses of BaseWait must implement method _on_response")

    async def on_response(self, response: Response):
        if not self.get_wait():
            return

        if not response.ok:
            return

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return

        await self._on_response(response)

    async def scroll_to_bottom(self, page: Page):
        await page.wait_for_timeout(1000)

        while True:
            last_height = await page.evaluate("document.body.scrollHeight")

            # 内部循环，每次滚动一个窗口的高度，直到滚动到页面底部
            while True:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                # 等待滚动动画和懒加载内容
                await page.wait_for_timeout(250)

                # 检查是否已到达页面底部
                is_at_bottom = await page.evaluate(
                    "window.scrollY + window.innerHeight >= document.body.scrollHeight"
                )
                if is_at_bottom:
                    break

            # 滚动到底部后，等待一段时间让新内容加载
            await page.wait_for_timeout(1000)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break

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
