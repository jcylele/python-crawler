
from Consts import WorkerType
from Workers.AnalysePostWorker import AnalysePostWorker
from Workers.BaseWorker import BaseWorker
from Workers.FetchActorWorker import FetchActorWorker
from Workers.FetchActorsWorker import FetchActorsWorker
from Workers.FileDownWorker import FileDownWorker
from Workers.PageDownWorker import PageDownWorker
from Workers.ResInfoWorker import ResInfoWorker
from Workers.ResValidWorker import ResValidWorker
from Workers.SimpleFileDownWorker import SimpleFileDownWorker

# specify the corresponding class for each worker type
WorkerClasses = {
    WorkerType.FileDown: FileDownWorker,
    WorkerType.PageDown: PageDownWorker,
    WorkerType.AnalysePost: AnalysePostWorker,
    WorkerType.ResInfo: ResInfoWorker,
    WorkerType.ResValid: ResValidWorker,
    WorkerType.SimpleFile: SimpleFileDownWorker,
    WorkerType.FetchActors: FetchActorsWorker,
    WorkerType.FetchActor: FetchActorWorker,
}

# specify worker count for types, count is 1 if not specified
WorkerCount = {
    WorkerType.PageDown: 3,
    WorkerType.FileDown: 7,
    WorkerType.ResInfo: 5,
    # WorkerType.FetchActor: 3,
}


def createWorker(work_type: WorkerType, task: 'DownloadTask') -> BaseWorker:
    """
    create a worker by type
    """
    cls = WorkerClasses.get(work_type)
    if not cls:
        raise NotImplementedError(f"WorkerType {work_type} Class Not Exist")
    return cls(task)


def getWorkerCount(work_type: WorkerType) -> int:
    """
    get configured worker count of the type
    :param work_type:
    :return:
    """
    count = WorkerCount.get(work_type)
    # default number
    if count is None:
        count = 1
    return count
