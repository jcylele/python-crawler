from Consts import WorkerType
from Ctrls import CommonCtrl, DbCtrl
from Utils import LogUtil
from WorkQueue.ExtraInfo import ResInfoExtraInfo
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseRequestWorker import BaseRequestWorker


class ResInfoWorker(BaseRequestWorker):
    """
    worker to get the size of a resource from the header
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.ResInfo, task=task)

    async def _process(self, item: UrlQueueItem) -> bool:
        extra_info: ResInfoExtraInfo = item.extra_info
        download_limit = self.DownloadLimit()
        # skip (avoid DDOS protection)
        if download_limit.isSkipResInfo(extra_info.res_type):
            return True

        succeed, size = await self._head(item)
        if not succeed:
            LogUtil.warning(f"head failed: {item.url}")
            return False

        # keep session life short, no time-consuming things allowed
        # so head first, then start session
        with DbCtrl.getSession() as session, session.begin():
            res1 = CommonCtrl.getRes(session, extra_info.res_id)

            # update size
            res1.setSize(size)

            # skip files which are too large for now
            if not download_limit.checkResSize(size):
                LogUtil.info(f"{extra_info} too big: {size:,d}")
                return True

            # enqueue for downloading
            if res1.shouldDownload(download_limit):
                await self.queue_mgr().downloadResFile(item, res1.tmpFilePath(), size)

            return True
