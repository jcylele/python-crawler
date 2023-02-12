import threading

import LogUtil
from WorkQueue import QueueMgr
from WorkQueue.BaseQueueItem import BaseQueueItem
from Consts import WorkerType


class BaseWorker(threading.Thread):
    def __init__(self, worker_type: WorkerType):
        super().__init__()
        self.__reported = False
        self.__waiting = False
        self.__workerType = worker_type

    def workerType(self) -> WorkerType:
        return self.__workerType

    def _queueType(self) -> QueueMgr.QueueType:
        raise NotImplementedError("subclasses of BaseWorker must implement method _queueType")

    def run(self):
        while True:
            self.__waiting = True
            item = QueueMgr.get(self._queueType())
            self.__waiting = False
            try:
                LogUtil.debug(f"process {item}")
                if not self._process(item):
                    item.onFailed()
                    if item.canTry():
                        QueueMgr.add(self._queueType(), item)
            except BaseException as e:
                LogUtil.error(e)
                break

    def _process(self, item: BaseQueueItem) -> bool:
        raise NotImplementedError("subclasses of BaseWorker must implement method _process")

    def reportDeath(self):
        if self.is_alive():
            return
        if self.__reported:
            return
        LogUtil.error(f"{self} died!!!!!!!!!!")
        self.__reported = True

    def isWaiting(self) -> bool:
        return self.__waiting
