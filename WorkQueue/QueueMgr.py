# manager for queues

import queue
from enum import Enum, auto

from WorkQueue.BaseQueueItem import BaseQueueItem


class QueueType(Enum):
    PageDownload = auto()
    FileDownload = auto()
    AnalyseActors = auto()
    AnalyseUser = auto()
    AnalysePost = auto()
    ResInfo = auto()
    ResValid = auto()


__all_queues: dict[QueueType, queue.Queue] = {}


def init():
    global __all_queues
    # only time-consuming items need to be prioritized
    __all_queues = {
        QueueType.PageDownload: queue.PriorityQueue(),
        QueueType.AnalyseActors: queue.Queue(),
        QueueType.AnalyseUser: queue.Queue(),
        QueueType.AnalysePost: queue.Queue(),
        QueueType.ResInfo: queue.PriorityQueue(),
        QueueType.FileDownload: queue.PriorityQueue(),
        QueueType.ResValid: queue.Queue(),
    }


def empty() -> bool:
    """
    is all queues empty
    :return:
    """
    for queue_type, q in __all_queues.items():
        if q.qsize() > 0:
            return False
    return True


def runningReport() -> str:
    str_list = []
    for queue_type, q in __all_queues.items():
        if q.qsize() > 0:
            str_list.append(f"{queue_type.name}:{q.qsize()}")
    return f"Queues: {','.join(str_list)}"


def put(queue_type: QueueType, item: BaseQueueItem):
    """
    put queue item into the queue.
    """
    # thread will wait if the queue is full
    # but waiting for put inside a session causes db conflicts
    # so all queues are infinite in size
    __all_queues[queue_type].put(item)


def get(queue_type: QueueType) -> BaseQueueItem:
    """
    get an item from the queue, wait if the queue is empty
    """
    return __all_queues[queue_type].get()
