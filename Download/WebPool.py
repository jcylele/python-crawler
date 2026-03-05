import asyncio

from playwright.async_api import Browser, Page, Playwright, async_playwright

import Configs
from Consts import CacheKey, WorkerType

__semaphores = {
    WorkerType.FetchActors: asyncio.Semaphore(1),
    WorkerType.FetchActorLink: asyncio.Semaphore(1),
    WorkerType.FetchActor: asyncio.Semaphore(2),
    WorkerType.FetchPost: asyncio.Semaphore(4),
}

# 全局 Playwright 实例
__playwright: Playwright | None = None
__browser: Browser | None = None


async def init_pool():
    """惰性初始化 Playwright 实例和浏览器。"""
    global __playwright, __browser
    if __browser is None:
        __playwright = await async_playwright().start()
        __browser = await __playwright.chromium.launch(headless=not Configs.getSetting(CacheKey.ShowBrowser))


async def acquire_page() -> Page:
    return await __browser.new_page()


async def release_page(page: Page):
    await page.close()


async def acquire_page_semaphore(worker_type: WorkerType):
    """申请信号量许可"""
    await __semaphores[worker_type].acquire()


def release_page_semaphore(worker_type: WorkerType):
    """释放信号量许可"""
    __semaphores[worker_type].release()


async def clear_pool():
    """优雅地关闭所有队列、浏览器和 Playwright 服务。"""
    global __playwright, __browser
    if __browser:
        await __browser.close()
        __browser = None
    if __playwright:
        # playwright.stop() 是同步的，不需要 await
        await __playwright.stop()
        __playwright = None
