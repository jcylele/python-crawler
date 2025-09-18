import asyncio

from playwright.async_api import async_playwright, Playwright, Browser, Page

import Configs
from Consts import WorkerType

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
        __browser = await __playwright.chromium.launch(headless=not Configs.SHOW_BROWSER)


async def acquire_page(worker_type: WorkerType) -> Page:
    """从浏览器获取一个新页面，受信号量控制"""
    semaphore = __semaphores[worker_type]
    await semaphore.acquire()  # 获取许可，如果许可没了就异步等待

    # 每次都创建一个新页面，因为页面状态不是独立的
    page = await __browser.new_page()
    return page


async def release_page(page: Page, worker_type: WorkerType):
    """关闭页面并释放信号量许可"""
    # 协程不能直接调用，所以我们需要一个包装
    # 更好的方式是在 worker 的 finally 块中处理
    semaphore = __semaphores[worker_type]
    semaphore.release()
    # 必须在事件循环中关闭页面
    await page.close()


async def clear_pool():
    """优雅地关闭所有队列、浏览器和 Playwright 服务。"""
    global __playwright, __browser
    if __browser:
        await __browser.close()
        __browser = None
    if __playwright:
        # playwright.stop() 是同步的，不需要 await
        __playwright.stop()
        __playwright = None
