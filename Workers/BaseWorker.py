import threading

from Consts import WorkerType, QueueType
from Download.DownloadLimit import DownloadLimit
from Utils import LogUtil
from WorkQueue import QueueMgr
from WorkQueue.BaseQueueItem import BaseQueueItem


class BaseWorker(threading.Thread):
    """
    base class of the work threads on the queues
    """

    def __init__(self, worker_type: WorkerType, task: 'DownloadTask'):
        super().__init__()
        self.__waiting = False
        self.__stop = False
        self.__workerType = worker_type
        self.task = task

    def QueueMgr(self) -> QueueMgr:
        return self.task.queueMgr

    def DownloadLimit(self) -> DownloadLimit:
        return self.task.downloadLimit

    def workerType(self) -> WorkerType:
        return self.__workerType

    def _queueType(self) -> QueueType:
        """
        the type of the queue on which it works
        :return:
        """
        raise NotImplementedError("subclasses of BaseWorker must implement method _queueType")

    def run(self):
        while not self.__stop:
            # wait for work
            self.__waiting = True
            item = self.QueueMgr().get(self._queueType())
            self.__waiting = False
            processed = False
            try:
                LogUtil.debug(f"{self.workerType().name} process {item}")
                processed = self._process(item)
            except BaseException as e:  # unhandled exceptions in the process
                self._onException(item, e)
                # break
            finally:
                if not processed:
                    item.onFailed()
                    if item.shouldRetry():
                        self.QueueMgr().put(self._queueType(), item)

    def _process(self, item: BaseQueueItem) -> bool:
        """
        real process function, implemented by subclasses
        :param item: work item
        :return: process succeed or not
        """
        raise NotImplementedError("subclasses of BaseWorker must implement method _process")

    def _onException(self, item, e: BaseException):
        LogUtil.error(f"{self} process {item} and encounter {type(e)}({e})")

    def isWaiting(self) -> bool:
        return self.__waiting

    def Stop(self):
        self.__stop = True
