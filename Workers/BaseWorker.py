from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Download.DownloadTask import DownloadTask

import asyncio

from sqlalchemy.orm import Session

import Configs
from Consts import WorkerType
from Ctrls import CommonCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskQueueMgr import TaskQueueMgr
from Utils import LogUtil
from WorkQueue.BaseQueueItem import BaseQueueItem, SentinelQueueItem


class BaseWorker:
    """
    base class of the work threads on the queues
    """

    def __init__(self, worker_type: WorkerType, task: DownloadTask):
        self.__workerType = worker_type
        self.__queueType = Configs.getQueueTypeByWorkerType(worker_type)
        self.task: DownloadTask = task

    def queue_mgr(self) -> TaskQueueMgr:
        return self.task.queue_mgr

    def DownloadLimit(self) -> DownloadLimit:
        return self.task.download_limit

    def init_group_id(self) -> int:
        return self.task.init_group_id

    def workerType(self) -> WorkerType:
        return self.__workerType

    def hasActorFolder(self, session: Session, actor_id: int) -> bool:
        actor = CommonCtrl.getActor(session, actor_id)
        return actor.actor_group.has_folder

    async def putback_item(self, item: BaseQueueItem):
        LogUtil.warning(f"{self.workerType().name} requeueing item: {item}")
        if not await self.queue_mgr().requeueItem(self.__queueType, item):
            self.task.onItemFailed(self.workerType())

    async def get_item(self) -> BaseQueueItem:
        return await self.queue_mgr().get(self.__queueType)

    def item_done(self):
        self.queue_mgr().item_done(self.__queueType)

    async def run(self):
        """
        这个方法现在是 Worker 的主协程。
        它将被 asyncio.create_task() 包装成一个任务来执行。
        """
        # LogUtil.info(f"{self.workerType().name}({self.task.desc}) worker started.")
        try:
            await self._onStart()
            while True:
                # LogUtil.info(
                #     f"{self.workerType().name} worker waiting for item...")
                item = await self.get_item()
                if isinstance(item, SentinelQueueItem):
                    self.item_done()
                    # LogUtil.info(
                    #     f"{self.workerType().name}  received sentinel, shutting down.")
                    break
                await self.queue_mgr().add_worker(self.__queueType)
                # LogUtil.info(f"{self.workerType().name} worker got item: {item}")
                processed = False
                try:
                    LogUtil.debug(f"{self.workerType().name} process {item}")
                    start_time = time.time()
                    processed = await self._process(item)
                    if processed:
                        self.task.onItemProcessed(
                            self.workerType(), time.time() - start_time)
                    else:
                        await self.putback_item(item)
                except asyncio.CancelledError:
                    # await self.putback_item(item)
                    raise
                except Exception as e:  # unhandled exceptions in the process
                    self._onException(item, e)
                    await self.putback_item(item)
                finally:
                    self.item_done()
                    await self.queue_mgr().remove_worker(self.__queueType)
        except asyncio.CancelledError:
            LogUtil.info(
                f"{self.workerType().name} worker cancelling...")
        except Exception as e:
            LogUtil.error(
                f"Worker {self.workerType().name} encounter error:")
            LogUtil.exception(e)
        finally:
            await self._onStop()

    async def _onStart(self):
        """
        called when the worker is started
        :return:
        """
        pass

    async def _onStop(self):
        """
        called when the worker is stopped
        :return:
        """
        pass

    async def _process(self, item: BaseQueueItem) -> bool:
        """
        real process function, implemented by subclasses
        :param item: work item
        :return: process succeed or not
        """
        raise NotImplementedError(
            "subclasses of BaseWorker must implement method _process")

    def _onException(self, item, e: BaseException):
        LogUtil.error(f"{self} process {item} and encounter error")
        LogUtil.exception(e)
