from enum import Enum, auto, IntEnum


class WorkerType(Enum):
    """
    worker type, find corresponding worker classes in WorkerMgr.py
    """
    FileDown = auto()
    PageDown = auto()
    ResInfo = auto()

    FetchActors = auto()
    FetchActor = auto()

    AnalysePost = auto()

    ResValid = auto()
    SimpleFile = auto()


class QueueType(IntEnum):
    AnalysePost = 3
    ResValid = 4

    FetchActors = 11
    FetchActor = 12

    MinPriorityQueue = 100

    PageDownload = 101
    FileDownload = 102
    ResInfo = 103
    SimpleFile = 104
