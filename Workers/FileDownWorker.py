import asyncio
import aiofiles.os  # 1. 导入 aiofiles.os

from Consts import WorkerType, QueueType
from Ctrls import DbCtrl, RequestCtrl
from Download import FileManager
from Utils import LogUtil
from WorkQueue.ExtraInfo import ResFileExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker

# resume uncompleted files which are large enough
# in case that the content is just error msg
MinResumeSize = 1024 * 1024


class FileDownWorker(BaseRequestWorker):
    """
    worker to download resource by url and save it to file
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.FileDown, task=task)

    def check_has_folder(self, extra_info: ResFileExtraInfo):
        with DbCtrl.getSession() as session, session.begin():
            return self.hasActorFolder(session, extra_info.actor_info.actor_id)

    async def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResFileExtraInfo = item.extra_info
        file_path = extra_info.file_path
        
        if not self.check_has_folder(extra_info):
            return True

        request_headers = RequestCtrl.createRequestHeaders()
        request_headers["referer"] = item.from_url
        # 3. 文件锁需要用 asyncio.Lock 实现，而不是依赖线程 ID
        async with FileManager.get_lock(file_path):
            # 4. 检查文件大小等操作全部替换为异步版本
            file_mode = "wb"

            if await aiofiles.os.path.exists(file_path):
                file_size = (await aiofiles.os.stat(file_path)).st_size
                if file_size == extra_info.file_size:
                    await self.queue_mgr().enqueueResValid(item)
                    return True

                if file_size >= MinResumeSize:
                    file_mode = "ab"
                    # 5. 关键修改：将 Range 头放入本次请求专用的 headers 字典
                    request_headers["Range"] = f"bytes={file_size}-"
                    LogUtil.warning(f"Resuming {file_path} from {file_size:,d}")

            # 6. 下载限流检查 (假设 DownloadLimit 已被改造或为非阻塞)
            if not self.DownloadLimit().canDownload(extra_info.file_size):
                return True

            try:
                # 7. 将专用的 headers 字典传递给下载方法
                await self._downloadStream(item.url, file_path, file_mode, headers=request_headers)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                LogUtil.exception(e)
                # 下载失败时，不继续执行后续逻辑
                return False
            finally:
                # 8. 无需清理 session headers，因为我们没有修改它
                pass

        # 9. 移出 lock 范围后再入队
        await self.queue_mgr().enqueueResValid(item)

        return True
