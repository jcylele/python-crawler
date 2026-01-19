import asyncio
from sqlalchemy.orm import Session
from playwright.async_api import Page, Locator, Response, Route, TimeoutError as PlaywrightTimeoutError

import Configs
from Consts import WorkerType
from Ctrls import CommonCtrl, DbCtrl, ActorCtrl
from Models.ModelInfos import ActorInfo
from Utils import LogUtil
from Download import WebPool
from WorkQueue.BaseQueueItem import BaseQueueItem
from Workers.BaseWorker import BaseWorker


class BaseFetchWorker(BaseWorker):
    """
    base class for workers working through webdriver
    """

    def __init__(self, worker_type: WorkerType, task):
        super().__init__(worker_type, task)

    def getActorInfo(self, actor_id: int) -> ActorInfo:
        with DbCtrl.getSession() as session, session.begin():
            return CommonCtrl.getActorInfo(session, actor_id)

    async def processActors(self, actor_infos: list[ActorInfo]) -> list[int]:
        all_actor_ids = []
        new_actor_ids = []
        with DbCtrl.getSession() as session, session.begin():
            for actor_info in actor_infos:
                # enqueue actor if not exists
                actor = ActorCtrl.getActorByInfo(session, actor_info)
                if actor is None:
                    self.DownloadLimit().onActor()
                    actor = ActorCtrl.addActor(
                        session, actor_info, self.init_category())
                    new_actor_ids.append(actor.actor_id)

                actor.favorite_count = actor_info.favorite_count
                all_actor_ids.append(actor.actor_id)

        for actor_id in new_actor_ids:
            await self.queue_mgr().enqueueFetchActor(actor_id)
            await self.queue_mgr().enqueueFetchActorLink(actor_id)

        return all_actor_ids

    async def calcActorInfo(self, actor_locator: Locator) -> ActorInfo:
        href = await actor_locator.get_attribute("href")
        if not href:
            raise SystemError("actor href attribute not found")
        href_list = href.split("/")
        # platform and link are already in href_list
        actor_info = ActorInfo()
        actor_info.actor_platform = href_list[-3]
        actor_info.actor_link = href_list[-1]
        # name
        actor_name_locator = actor_locator.locator(".user-card__name")
        actor_name = await actor_name_locator.text_content()
        if not actor_name:
            if (await actor_name_locator.count()) == 0:
                raise SystemError("actor name element not found")
            raise SystemError("actor name is empty")

        actor_info.actor_name = actor_name.strip()

        # favorite count
        fav_locator = actor_locator.locator(".user-card__count b")
        if (await fav_locator.count()) > 0:
            fav_count = await fav_locator.text_content()
            if fav_count and fav_count.strip():
                try:
                    actor_info.favorite_count = int(fav_count.strip())
                except ValueError:
                    pass

        return actor_info

    async def scrollToBottom(self, page: Page):
        await page.wait_for_timeout(1000)

        while True:
            last_height = await page.evaluate("document.body.scrollHeight")

            # 内部循环，每次滚动一个窗口的高度，直到滚动到页面底部
            while True:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                # 等待滚动动画和懒加载内容
                await page.wait_for_timeout(200)

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

    async def _thumbnail_block_handler(self, route: Route):
        request = route.request

        # abort thumbnail request
        if request.resource_type == "image":
            pure_file_name = Configs.regex_thumbnail_file_name(request.url)
            if pure_file_name:
                await route.abort()
                return

        await route.continue_()

    async def _onFetched(self, item: BaseQueueItem, page: Page) -> bool:
        raise NotImplementedError(
            "subclasses of BaseFetchWorker must implement method _onFetched")

    def _loadSelector(self) -> str:
        raise NotImplementedError(
            "subclasses of BaseFetchWorker must implement method _loadSelector")

    def _url(self, item: BaseQueueItem) -> str:
        raise NotImplementedError(
            "subclasses of BaseFetchWorker must implement method _url")

    def _checkFetch(self, session: Session, item: BaseQueueItem):
        """check if the item should be fetched"""
        raise NotImplementedError(
            "subclasses of BaseFetchWorker must implement method _checkFetch")

    def _beforeFetch(self, session: Session, item: BaseQueueItem):
        """do some extra work before fetching"""
        pass

    async def _setup_page(self, page: Page):
        """钩子：允许子类在页面导航前进行设置 (如请求拦截)"""
        pass

    async def on_response(response: Response):
        pass

    async def _process(self, item: BaseQueueItem) -> bool:
        with DbCtrl.getSession() as session, session.begin():
            if not self._checkFetch(session, item):
                return True
            self._beforeFetch(session, item)

        page = None
        try:
            page = await WebPool.acquire_page(self.workerType())
            await self._setup_page(page)
            page.on("response", self.on_response)
            await page.goto(self._url(item), timeout=60000)
            fetch_succeed = False
            for i in range(30):
                try:
                    # Wait for the main content selector to ensure the page is loaded
                    await page.wait_for_selector(self._loadSelector(), timeout=10000)
                    # If selector is found, break the loop and proceed
                    fetch_succeed = True
                    break
                except PlaywrightTimeoutError:
                    title = await page.title()
                    LogUtil.info(
                        f"failed to load {item}, get {title} instead (attempt {i+1}/30)")

                    if "DDoS-Guard" in title:
                        LogUtil.info(
                            "DDoS-Guard detected, waiting for human intervention...")
                        await asyncio.sleep(10)
                        await page.reload()
                    elif "Error" in title:
                        LogUtil.info("Error page detected, refreshing...")
                        await asyncio.sleep(10)
                        await page.reload()
                    else:
                        LogUtil.warning(
                            f"Page load timeout, title '{title}', retrying...")
                        await asyncio.sleep(10)
                        await page.reload()

            if fetch_succeed:
                processed = await self._onFetched(item, page)
                return processed
            else:
                LogUtil.error(f"Failed to load page for {item}, Giving up.")
                return False
        finally:
            if page:
                await WebPool.release_page(page, self.workerType())
