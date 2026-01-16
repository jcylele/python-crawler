import asyncio
import math

from playwright.async_api import Page, Response, expect, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.orm import Session

from Consts import WorkerType
from Ctrls import ActorCtrl, ActorQueryCtrl, DbCtrl, RequestCtrl
from Models.ActorModel import ActorModel
from Models.ModelInfos import ActorInfo
from Utils import CacheUtil, LogUtil
from WorkQueue.BaseQueueItem import BaseQueueItem
from WorkQueue.FetchQueueItem import FetchActorsQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker
from Workers.ImageWait.ActorIconsWait import ActorIconsWait


class FetchActorsWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.FetchActors, task=task)
        self.actor_icons_wait = ActorIconsWait()

    def getFinishedPage(self, start_page: int) -> int:
        if start_page > 0:
            return start_page - 1
        if start_page == 0:
            return 0
        with DbCtrl.getSession() as session, session.begin():
            actor_count = ActorQueryCtrl.getAllActorCount(session)
            return math.floor(actor_count / 50)

    def _loadSelector(self) -> str:
        return '#paginator-top menu'

    def _url(self, item: FetchActorsQueueItem) -> str:
        self.start_page = self.getFinishedPage(item.start_page) + 1
        LogUtil.info(f"fetch actors from page {self.start_page}")
        return RequestCtrl.formatActorsUrl((self.start_page - 1) * 50)

    def _checkFetch(self, session: Session, item: BaseQueueItem):
        return True

    def _beforeFetch(self, session: Session, item: BaseQueueItem):
        self.actor_icons_wait.set_actor_infos([])

    async def on_response(self, response: Response):
        await self.actor_icons_wait.on_response(response)

    async def _onFetched(self, item: FetchActorsQueueItem, page: Page) -> bool:
        while True:
            try:
                top_menu = page.locator(self._loadSelector())
                # 使用 expect 等待当前页码加载正确，这是页面跳转后的主要同步点
                current_page_locator = top_menu.locator(
                    ".pagination-button-current b")
                await expect(current_page_locator).to_have_text(str(self.start_page), timeout=10000)

            except PlaywrightTimeoutError:
                LogUtil.error(
                    f"actors page {self.start_page} not found or timed out.")
                break

            current_page_text = await current_page_locator.text_content()
            LogUtil.info(f"fetch actors page {current_page_text}")

            # 分析内容
            actor_locators = await page.locator('a.user-card').all()
            actor_infos = []
            for actor_locator in actor_locators:
                try:
                    actor_info = await self.calcActorInfo(actor_locator)
                    actor_infos.append(actor_info)
                except SystemError as e:
                    LogUtil.warning(f"Failed to parse an actor card: {e}")

            await self.processActors(actor_infos)

            self.actor_icons_wait.set_actor_infos(actor_infos)
            await self.actor_icons_wait.wait(page)

            # 寻找下一页按钮
            next_btn_locator = top_menu.locator(
                '.pagination-button-after-current')

            # 检查下一页按钮是否存在
            if (await next_btn_locator.count()) == 0:
                LogUtil.info(
                    f"No next button, page {current_page_text} is the last page.")
                break

            if not self.DownloadLimit().moreActor():
                LogUtil.info("Actor download limit reached.")
                break

            self.start_page += 1

            # slow down to avoid being blocked
            await asyncio.sleep(2)
            # 点击下一页，循环开始时会等待新页面加载
            await next_btn_locator.click()

        if item.start_page >= 0:
            CacheUtil.setCustomPage(self.start_page)
            LogUtil.info(f"set custom page to {self.start_page}")

        return True
