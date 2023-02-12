import queue
from enum import Enum, auto

from WorkQueue.BaseQueueItem import BaseQueueItem


class QueueType(Enum):
    Download = auto()
    AnalyseActors = auto()
    AnalyseUser = auto()
    AnalysePost = auto()
    ResInfo = auto()
    ResFile = auto()
    ResValid = auto()


all_queues: dict[QueueType, queue.Queue] = {}


def init():
    global all_queues
    all_queues = {
        QueueType.Download: queue.PriorityQueue(),
        QueueType.AnalyseActors: queue.Queue(),
        QueueType.AnalyseUser: queue.Queue(),
        QueueType.AnalysePost: queue.Queue(),
        QueueType.ResInfo: queue.PriorityQueue(),
        QueueType.ResFile: queue.PriorityQueue(),
        QueueType.ResValid: queue.Queue(),
    }


def empty() -> bool:
    for queue_type, q in all_queues.items():
        if q.qsize() > 0:
            return False
    return True


def report():
    str_list = []
    for queue_type, q in all_queues.items():
        if q.qsize() > 0:
            str_list.append(f"{queue_type.name}:{q.qsize()}")
    return f"Queues: {','.join(str_list)}"


def add(queue_type: QueueType, item: BaseQueueItem):
    # LogUtil.info(f"add {item} to {queue_type.name}")
    all_queues[queue_type].put(item)


def get(queue_type: QueueType) -> BaseQueueItem:
    return all_queues[queue_type].get()
