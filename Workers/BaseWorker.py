import threading

from Consts import WorkerType
from Utils import LogUtil
from WorkQueue import QueueMgr
from WorkQueue.BaseQueueItem import BaseQueueItem


class BaseWorker(threading.Thread):
    """
    base class of the work threads on the queues
    """

    def __init__(self, worker_type: WorkerType):
        super().__init__()
        self.__waiting = False
        self.__workerType = worker_type

    def workerType(self) -> WorkerType:
        return self.__workerType

    def _queueType(self) -> QueueMgr.QueueType:
        """
        the type of the queue on which it works
        :return:
        """
        raise NotImplementedError("subclasses of BaseWorker must implement method _queueType")

    def run(self):
        while True:
            # wait for work
            self.__waiting = True
            item = QueueMgr.get(self._queueType())
            self.__waiting = False
            try:
                LogUtil.debug(f"{self.workerType().name} process {item}")
                if not self._process(item):
                    item.onFailed()
                    if item.shouldRetry():
                        QueueMgr.put(self._queueType(), item)
            except BaseException as e:  # unhandled exceptions in the process
                LogUtil.error(f"{self} died of {type(e)}({e.args})")
                break

    def _process(self, item: BaseQueueItem) -> bool:
        """
        real process function, implemented by subclasses
        :param item: work item
        :return: process succeed or not
        """
        raise NotImplementedError("subclasses of BaseWorker must implement method _process")

    def isWaiting(self) -> bool:
        return self.__waiting
