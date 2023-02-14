
from Consts import WorkerType
from Workers.AnalyseActorWorker import AnalyseActorWorker
from Workers.AnalyseActorsWorker import AnalyseActorsWorker
from Workers.AnalysePostWorker import AnalysePostWorker
from Workers.BaseWorker import BaseWorker
from Workers.FileDownWorker import FileDownWorker
from Workers.PageDownWorker import PageDownWorker
from Workers.ResInfoWorker import ResInfoWorker
from Workers.ResValidWorker import ResValidWorker

# specify the corresponding class for each worker type
WorkerClasses = {
    WorkerType.FileDown: FileDownWorker,
    WorkerType.PageDown: PageDownWorker,
    WorkerType.AnalyseActors: AnalyseActorsWorker,
    WorkerType.AnalyseActor: AnalyseActorWorker,
    WorkerType.AnalysePost: AnalysePostWorker,
    WorkerType.ResInfo: ResInfoWorker,
    WorkerType.ResValid: ResValidWorker,

}

# specify worker count for types, count is 1 if not specified
WorkerCount = {
    WorkerType.PageDown: 10,
    WorkerType.FileDown: 10,
    WorkerType.ResInfo: 10,
}


def createWorker(work_type: WorkerType) -> BaseWorker:
    """
    create a worker by type
    :param work_type:
    :return:
    """
    cls = WorkerClasses.get(work_type)
    if not cls:
        raise NotImplementedError(f"WorkerType {work_type} Class Not Exist")
    return cls()


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
