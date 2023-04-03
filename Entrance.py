import os.path
from enum import Enum, auto

import Configs
import Consts
from Ctrls import ActorCtrl, DbCtrl, ResCtrl
from Guarder import Guarder
from Models.BaseModel import ActorCategory
from Utils import LogUtil
from WorkQueue import QueueMgr, QueueUtil
from Workers import WorkerMgr

StrActorName = "input actor's name: "
StrOnlyInfo = "all but only info[y] or normal download[n]: "
StrNewActors = "new actors(y) or current actors(n): "
StrMoreSample = "more sample(y) or normal sample(n): "


class MainOperation(Enum):
    """
    configuration to begin the process
    """
    DownOne = auto()
    DownLiked = auto()
    DownSample = auto()
    LikeAll = auto()

    @property
    def Desc(self):
        if self == MainOperation.DownOne:
            return "download almost all posts of one actor"
        elif self == MainOperation.DownLiked:
            return "download some posts of all actors you liked"
        elif self == MainOperation.DownSample:
            return "download few samples of new actors"
        elif self == MainOperation.LikeAll:
            return "mark all remain actors as liked"
        return None

    @staticmethod
    def formatMainOperationTip():
        str_list = []
        for op in MainOperation:
            str_list.append(f"[{op.value}] {op.Desc}")
        str_list.append("input your operation number: ")
        return str_list


def setWorkerCount(worker_type: Consts.WorkerType, count: int):
    WorkerMgr.WorkerCount[worker_type] = count


def startDownload():
    """
    new all threads and start running
    :return:
    """
    guarder = Guarder()
    for work_type in Consts.WorkerType:
        count = WorkerMgr.getWorkerCount(work_type)
        for i in range(count):
            worker = WorkerMgr.createWorker(work_type)
            guarder.addWorker(worker)
    guarder.start()


def downloadActors(actor_names: list[str]):
    """
    download an actor only
    """
    for actor_name in actor_names:
        QueueUtil.enqueueActor(actor_name)
    startDownload()


def downloadNewActors():
    """
    download new actors
    :return:
    """
    QueueUtil.enqueueActors()
    startDownload()


def downloadByActorCategory(actor_category: ActorCategory):
    """
    download actors in corresponding category
    :param actor_category: category to filter actors
    :return:
    """
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.getActorsByCategory(session, actor_category)
        for actor in actors:
            QueueUtil.enqueueActor(actor.actor_name)
    startDownload()


def likeAllActors():
    """
    mark all existing  actors as liked
    :return:
    """
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.favorAllInitActors(session)


def repairRecords():
    """
    refresh database according to the existence of files and folders
    :return:
    """
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.repairRecords(session)
    with DbCtrl.getSession() as session, session.begin():
        ResCtrl.repairRecords(session)


def initEnv():
    """
    initialize the environment
    :return:
    """
    LogUtil.info("initializing...")
    os.makedirs(Configs.RootFolder, exist_ok=True)
    os.makedirs(Configs.formatTmpFolderPath(), exist_ok=True)
    os.makedirs(Configs.formatIconFolderPath(), exist_ok=True)
    DbCtrl.init()
    QueueMgr.init()
    # repairRecords()


def enter():
    initEnv()
    for tip in MainOperation.formatMainOperationTip():
        LogUtil.info(tip)
    op = input()
    eop = MainOperation(int(op))
    if eop == MainOperation.DownLiked:
        is_all = input(StrOnlyInfo)
        if is_all == 'y':
            Configs.setConfig(0, 10000, 0)
        elif is_all == 'n':
            Configs.setConfig(0, 100, 100 * 1024 * 1024)
        else:
            raise Exception(f"invalid option {is_all}")
        downloadByActorCategory(ActorCategory.Liked)
    elif eop == MainOperation.DownSample:
        is_new = input(StrNewActors)
        if is_new == 'y':
            Configs.setConfig(50, 50, 20 * 1024 * 1024)
            downloadNewActors()
        elif is_new == 'n':
            is_more = input(StrMoreSample)
            if is_more == 'y':
                Configs.setConfig(0, 100, 100 * 1024 * 1024)
            elif is_more == 'n':
                Configs.setConfig(50, 50, 20 * 1024 * 1024)
            else:
                raise Exception(f"invalid option {is_more}")
            downloadByActorCategory(ActorCategory.Init)
        else:
            raise Exception(f"invalid option {is_new}")
    elif eop == MainOperation.DownOne:
        actor_name = input(StrActorName)
        Configs.setConfig(0, 10000, 1024 * 1024 * 1024)
        downloadActor(actor_name)
    elif eop == MainOperation.LikeAll:
        likeAllActors()
    else:
        LogUtil.error(f"invalid option {eop}")
