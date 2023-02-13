from enum import Enum, auto

import Configs
import Consts
import LogUtil
from Ctrls import ActorCtrl, CtrlUtil, ResCtrl
from Guarder import Guarder
from Models.BaseModel import ActorTag
from WorkQueue import QueueMgr, QueueUtil
from Workers import WorkUtil

StrActorName = "input actor's name: "
StrOnlyInfo = "all but only info[y] or normal download[n]: "
StrNewActors = "new actors(y) or current actors(n): "
StrMoreSample = "more sample(y) or normal sample(n): "


class MainOperation(Enum):
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


def setConfig(config_type: Configs.ConfigType):
    Configs.setConfig(config_type)


def setWorkerCount(worker_type: Consts.WorkerType, count: int):
    WorkUtil.WorkerCount[worker_type] = count


def startDownload():
    guarder = Guarder()
    for work_type in Consts.WorkerType:
        count = WorkUtil.getWorkerCount(work_type)
        for i in range(count):
            worker = WorkUtil.createWorker(work_type)
            guarder.addWorker(worker)
    guarder.start()


def removeInvalidRes():
    with CtrlUtil.getSession() as session, session.begin():
        ResCtrl.removeInvalidRes(session)


def downloadActor(actor_name: str):
    QueueUtil.enqueueActor(actor_name)
    startDownload()


def downloadNewActors():
    QueueUtil.enqueueActors()
    startDownload()


def downloadByActorTag(actor_tag: ActorTag):
    with CtrlUtil.getSession() as session, session.begin():
        actors = ActorCtrl.getActorsByTag(session, actor_tag)
        for actor in actors:
            QueueUtil.enqueueActor(actor.actor_name)
    startDownload()


def likeAllActors():
    with CtrlUtil.getSession() as session, session.begin():
        ActorCtrl.likeAllActors(session)


def repairRecords():
    with CtrlUtil.getSession() as session, session.begin():
        ActorCtrl.repairRecords(session)
    with CtrlUtil.getSession() as session, session.begin():
        ResCtrl.repairRecords(session)


def initEnv():
    LogUtil.info("initializing...")
    CtrlUtil.init()
    QueueMgr.init()
    repairRecords()


def enter():
    initEnv()
    for tip in MainOperation.formatMainOperationTip():
        LogUtil.info(tip)
    op = input()
    eop = MainOperation(int(op))
    if eop == MainOperation.DownLiked:
        is_all = input(StrOnlyInfo)
        if is_all == 'y':
            setConfig(Configs.ConfigType.All)
            setWorkerCount(Consts.WorkerType.FileDown, 0)
        elif is_all == 'n':
            setConfig(Configs.ConfigType.Liked)
        else:
            raise Exception(f"invalid option {is_all}")
        downloadByActorTag(ActorTag.Liked)
    elif eop == MainOperation.DownSample:
        is_new = input(StrNewActors)
        if is_new == 'y':
            setConfig(Configs.ConfigType.Sample)
            downloadNewActors()
        elif is_new == 'n':
            is_more = input(StrMoreSample)
            if is_more == 'y':
                setConfig(Configs.ConfigType.Liked)
            elif is_more == 'n':
                setConfig(Configs.ConfigType.Sample)
            else:
                raise Exception(f"invalid option {is_more}")
            downloadByActorTag(ActorTag.Init)
        else:
            raise Exception(f"invalid option {is_new}")
    elif eop == MainOperation.DownOne:
        actor_name = input(StrActorName)
        Configs.setConfig(Configs.ConfigType.All)
        downloadActor(actor_name)
    elif eop == MainOperation.LikeAll:
        likeAllActors()
    else:
        LogUtil.error(f"invalid option {eop}")
