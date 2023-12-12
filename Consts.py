from enum import Enum, auto, IntEnum


class ActorCategory(Enum):
    Init = 1  # initial state of an actor
    Liked = 2  # mark as liked
    Dislike = 3  # dislike and remove the folder
    Enough = 4  # once liked, then remove the folder


class ResType(Enum):
    Image = 1
    Video = 2


class ResState(Enum):
    Init = 1
    Down = 2
    Skip = 3
    Del = 4


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
