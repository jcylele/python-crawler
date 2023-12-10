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

    def clear(self):
        """
        clear all queues
        """
        for queue_type, q in self.__all_queues.items():
            q.queue.clear()

    def empty(self) -> bool:
        """
        is all queues empty
        :return:
        """
        for queue_type, q in self.__all_queues.items():
            if q.qsize() > 0:
                return False
        return True

    def getQueueCountMap(self) -> dict[str, int]:
        size_map = {}
        for queue_type, q in self.__all_queues.items():
            if q.qsize() > 0:
                size_map[queue_type.name] = q.qsize()
        return size_map

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
