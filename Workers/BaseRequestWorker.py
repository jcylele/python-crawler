import asyncio
import aiohttp
import aiofiles
from Consts import WorkerType
from Ctrls import RequestCtrl
from Utils import LogUtil
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker


class BaseRequestWorker(BaseWorker):
    """
    base class for workers working through request
    """

    def __init__(self, worker_type: WorkerType, task):
        super().__init__(worker_type, task)
        # 2. 创建一个 aiohttp 的 ClientSession
        #    它等同于 requests.Session，提供了连接池等功能
        # self.requestSession = aiohttp.ClientSession()

    async def run(self):
        """
        重写 run 方法来管理 session 的生命周期。
        """
        # 2. 在这里创建 session，此时事件循环肯定正在运行。
        self.requestSession = aiohttp.ClientSession()
        try:
            # 3. 调用父类的 run 方法来执行核心的工作循环。
            await super().run()
        finally:
            # 4. super().run() 的 finally 块会调用 _onStop，确保 session 被关闭。
            pass

    async def _onStop(self):
        """
        在 Worker 停止时被调用，确保 aiohttp session 被优雅关闭。
        """
        if not self.requestSession.closed:
            await self.requestSession.close()

    async def _head(self, item: UrlQueueItem) -> tuple[bool, int]:
        """
        异步获取 web 资源的大小
        """
        headers = RequestCtrl.createRequestHeaders()
        headers["referer"] = item.from_url
        try:
            async with self.requestSession.head(item.url, headers=headers, allow_redirects=False) as res:
                if res.status == 200:
                    content_length = res.headers.get('Content-Length')
                    return True, int(content_length) if content_length else 0
                elif res.status in (301, 302, 307, 308):  # redirect
                    item.from_url = item.url
                    url = res.headers['Location']
                    item.url = RequestCtrl.formatFullUrl(url)
                    # 6. 递归调用需要 await
                    return await self._head(item)
                elif res.status == 429 or res.status == 403:  # too fast
                    # 7. time.sleep() 必须替换为 await asyncio.sleep()
                    await asyncio.sleep(5)
                    LogUtil.warning(f"head {item.url} too fast")
                    return await self._head(item)
                else:
                    LogUtil.info(f"head error {res.status}: {item.url}")
                    return False, 0
        except Exception as e:
            LogUtil.error(f"head {item.url} failed")
            LogUtil.exception(e)
            return False, 0

    async def _download(self, item: UrlQueueItem) -> str | None:
        """
        异步下载网页内容
        """
        headers = RequestCtrl.createRequestHeaders()
        headers["referer"] = item.from_url
        try:
            async with self.requestSession.get(item.url, headers=headers, allow_redirects=False) as res:
                if res.status == 200:
                    # 8. 获取响应内容是异步操作
                    return await res.text()
                elif res.status in (301, 302, 307, 308):  # redirect
                    item.from_url = item.url
                    url = res.headers['Location']
                    item.url = RequestCtrl.formatFullUrl(url)
                    return await self._download(item)
                elif res.status == 429:  # too fast
                    await asyncio.sleep(5)
                    LogUtil.warning(f"get {item.extra_info} too fast")
                    return await self._download(item)
                else:
                    LogUtil.info(f"get error {res.status}: {item.url}")
                    return None
        except Exception as e:
            LogUtil.error(f"download {item.url} failed")
            LogUtil.exception(e)
            return None

    async def _downloadStream(self, url: str, file_path: str, file_mode: str = "wb", headers: dict | None = None):
        """
        使用 aiohttp 和 aiofiles 进行高效的异步流式下载
        """
        if headers is None:
            headers = RequestCtrl.createRequestHeaders()
        try:
            async with self.requestSession.get(url, headers=headers) as r:
                r.raise_for_status()  # 如果状态码不是 2xx，则抛出异常
                # 9. 使用 aiofiles 进行异步文件写入
                async with aiofiles.open(file_path, mode=file_mode) as f:
                    # 10. 以块（chunk）的方式异步读取和写入
                    while True:
                        chunk = await r.content.read(8192)  # 读取 8KB
                        if not chunk:
                            break
                        await f.write(chunk)
        except Exception as e:
            LogUtil.error(f"Stream download {url} failed")
            raise  # 重新抛出异常，让调用者知道失败了

    # 11. _downloadSmall 函数的功能完全可以被 _downloadStream 替代，建议移除
    #     如果确实需要保留，也必须用 aiohttp 和 aiofiles 重写
    # async def _downloadSmall(self, url: str, file_path: str) -> bool:
    #     try:
    #         await self._downloadStream(url, file_path)
    #         return True
    #     except:
    #         return False
