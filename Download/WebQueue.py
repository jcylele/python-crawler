import threading
from queue import LifoQueue, Empty
from playwright.async_api import Browser, BrowserContext, Page


class WebQueue(object):
    def __init__(self, max_count: int, browser: Browser):
        self.max_count = max_count
        self.created_count = 0
        self.browser = browser
        self.context: BrowserContext = self.browser.new_context()
        self.__queue: LifoQueue[Page] = LifoQueue()
        self.__lock = threading.Lock()

    def get(self) -> Page:
        """
        从池中获取一个页面。
        如果池中有可用的页面，立即返回。
        如果没有，并且尚未达到最大页面数，则创建一个新页面。
        如果已达到最大页面数，则阻塞等待，直到有页面被归还。
        """
        try:
            # 尝试非阻塞地从队列中获取一个页面
            return self.__queue.get(block=False)
        except Empty:
            # 队列为空，检查是否可以创建新页面
            # 使用锁来保护 created_count 的并发访问
            with self.__lock:
                if self.created_count < self.max_count:
                    self.created_count += 1
                    # 在持有锁的情况下创建页面，以确保计数准确
                    return self.context.new_page()

            # 已达到最大页面数，阻塞等待一个页面被归还
            return self.__queue.get(block=True)

    def put(self, page: Page):
        """将页面归还到池中。"""
        self.__queue.put(page)

    async def clear(self):
        """关闭此队列中的所有页面和浏览器上下文。"""
        # 清空队列，关闭所有页面
        while not self.__queue.empty():
            try:
                page = self.__queue.get(block=False)
                page.close()
            except Empty:
                break

        # 关闭上下文
        if self.context:
            await self.context.close()
