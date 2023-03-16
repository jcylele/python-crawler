from enum import Enum, auto


class WorkerType(Enum):
    """
    worker type, find corresponding worker classes in WorkerMgr.py
    """
    FileDown = auto()
    PageDown = auto()
    ResInfo = auto()

    AnalyseActors = auto()
    AnalyseActor = auto()
    AnalysePost = auto()

    ResValid = auto()
    SimpleFile = auto()
