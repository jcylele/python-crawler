from enum import Enum, auto

import Configs
import Consts
import LogUtil
from Ctrls import ActorCtrl, CtrlUtil, ResCtrl
from Guarder import Guarder
from Models.BaseModel import ActorTag
from WorkQueue import QueueMgr, QueueUtil
from Workers import WorkUtil


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


def testDb():
    with CtrlUtil.getSession() as session, session.begin():
        # actor = ActorCtrl.getActor(session, "kittyxkum")
        # actor.actor_tag = ActorTag.Enough

        # actors = ActorCtrl.getActorsByTag(session, ActorTag.Enough)
        # for actor in actors:
        #     print(actor)

        # post = PostCtrl.getPost(session, 482927298)
        # print(post)
        #
        # stmt = select(ResModel)
        # result = session.scalars(stmt)
        # for r in result:
        #     if r.post is None:
        #         print("None")

        # actors = ActorCtrl.getActorsByTag(session, ActorTag.Dislike)
        # for actor in actors:
        #     print(actor)

        # ResCtrl.removeInvalidRes(session)
        pass


class MainOp(Enum):
    DownOne = auto()
    DownLiked = auto()
    DownSample = auto()
    LikeAll = auto()


if __name__ == '__main__':
    for mop in MainOp:
        print(f"{mop}:{mop.value}")
    op = input("Choose your operation:")
    # op = MainOp.DownOne
    eop = MainOp(int(op))

    CtrlUtil.init()
    QueueMgr.init()
    repairRecords()
    if eop == MainOp.DownLiked:
        is_all = input("All But Only Info(y) or Normal Download(n):")
        if is_all == 'y':
            Configs.setConfig(Configs.ConfigType.All)
            WorkUtil.WorkerCount[Consts.WorkerType.FileDown] = 0
        elif is_all == 'n':
            Configs.setConfig(Configs.ConfigType.Liked)
        else:
            raise Exception(f"invalid option {is_all}")
        downloadByActorTag(ActorTag.Liked)
    elif eop == MainOp.DownSample:
        is_new = input("New Actors(y) or Current Actors(n):")
        if is_new == 'y':
            Configs.setConfig(Configs.ConfigType.Sample)
            downloadNewActors()
        elif is_new == 'n':
            is_more = input("More Sample(y) or Normal Sample(n):")
            if is_more == 'y':
                Configs.setConfig(Configs.ConfigType.Liked)
            elif is_more == 'n':
                Configs.setConfig(Configs.ConfigType.Sample)
            else:
                raise Exception(f"invalid option {is_more}")
            downloadByActorTag(ActorTag.Init)
        else:
            raise Exception(f"invalid option {is_new}")
    elif eop == MainOp.DownOne:
        actor_name = input("Input actor name:")
        Configs.setConfig(Configs.ConfigType.All)
        downloadActor(actor_name)
    elif eop == MainOp.LikeAll:
        likeAllActors()
    else:
        LogUtil.error("Wrong Operation")
    # pass
    # testDb()
