# manager for queues

import queue

from Consts import QueueType
from WorkQueue.BaseQueueItem import BaseQueueItem


class QueueMgr(object):
    """
    manager for queues
    """

    def __init__(self):
        self.__all_queues: dict[QueueType, queue.Queue] = {}
        for queue_type in QueueType:
            if queue_type > QueueType.MinPriorityQueue:
                self.__all_queues[queue_type] = queue.PriorityQueue()
            else:
                self.__all_queues[queue_type] = queue.Queue()

    def empty(self) -> bool:
        """
        is all queues empty
        :return:
        """
        for queue_type, q in self.__all_queues.items():
            if q.qsize() > 0:
                return False
        return True

    def runningReport(self) -> str:
        str_list = []
        for queue_type, q in self.__all_queues.items():
            if q.qsize() > 0:
                str_list.append(f"{queue_type.name}:{q.qsize()}")
        return f"Queues: {','.join(str_list)}"

    def put(self, queue_type: QueueType, item: BaseQueueItem):
        """
        put queue item into the queue.
        """
        # thread will wait if the queue is full
        # but waiting for put inside a session causes db conflicts
        # so all queues are infinite in size
        self.__all_queues[queue_type].put(item)

    def get(self, queue_type: QueueType) -> BaseQueueItem:
        """
        get an item from the queue, wait if the queue is empty
        """
        return self.__all_queues[queue_type].get()
