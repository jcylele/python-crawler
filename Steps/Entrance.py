from enum import Enum

import Configs
import Consts
import LogUtil
from Ctrls import ActorCtrl, CtrlUtil, ResCtrl
from Guarder import Guarder
from Models.BaseModel import ActorTag
from Steps.DataInputSteps import SetFieldStep, InputStep, MainOperation, BranchStep, EndStep, BaseStep
from Steps.InputConverters import IntEnumInputConverter, BoolInputConverter
from WorkQueue import QueueMgr, QueueUtil
from Workers import WorkUtil

StrActorName = "input actor's name: "
StrOnlyInfo = "all but only info[y] or normal download[n]: "
StrNewActors = "new actors(y) or current actors(n): "
StrMoreSample = "more sample(y) or normal sample(n): "


class DataFieldName(str, Enum):
    op = "op"
    actor_name = "actor_name"
    info_only = "info_only"
    is_new = "is_new"
    is_more = "is_more"


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


def onStepsEnd(input_data: dict):
    LogUtil.info(input_data)
    return

    op = input_data[DataFieldName.op]
    if op == MainOperation.DownOne:
        setConfig(Configs.ConfigType.All)
        downloadActor(input_data[DataFieldName.actor_name])
    elif op == MainOperation.DownLiked:
        if input_data[DataFieldName.info_only]:
            setConfig(Configs.ConfigType.All)
            setWorkerCount(Consts.WorkerType.FileDown, 0)
        else:
            setConfig(Configs.ConfigType.Liked)
        downloadByActorTag(ActorTag.Liked)
    elif op == MainOperation.DownSample:
        if input_data[DataFieldName.is_new]:
            setConfig(Configs.ConfigType.Sample)
            downloadNewActors()
        else:
            if input_data[DataFieldName.is_more]:
                setConfig(Configs.ConfigType.Liked)
            else:
                setConfig(Configs.ConfigType.Sample)
            downloadByActorTag(ActorTag.Init)
    elif op == MainOperation.LikeAll:
        likeAllActors()


def buildStep(step_json) -> BaseStep:
    if isinstance(step_json, list):
        next_step = None
        for i in range(len(step_json) - 1, -1, -1):
            cur_step = buildStep(step_json[i])
            if next_step is not None:
                cur_step.addNextStep(next_step)
            next_step = cur_step
        return next_step
    elif isinstance(step_json, tuple):
        (cls, *params) = step_json
        return cls(*params)
    elif isinstance(step_json, dict):
        ret = BranchStep()
        for key, step in step_json.items():
            next_step = buildStep(step)
            ret.addNextStep((key, next_step))
        return ret
    elif step_json == EndStep:
        return EndStep()
    else:
        raise RuntimeError(f"invalid step json: {step_json}")


def enter():
    """
    new start point
    try to separate input process and logic code
    not so elegant, just for practise
    :return:
    """
    # initEnv()

    step_json = [
        (InputStep, MainOperation.formatMainOperationTip(), MainOperation),
        (SetFieldStep, DataFieldName.op),
        {
            MainOperation.DownSample: [
                (InputStep, StrNewActors, bool),
                (SetFieldStep, DataFieldName.is_new),
                {
                    True: [EndStep],
                    False: [
                        (InputStep, StrMoreSample, bool),
                        (SetFieldStep, DataFieldName.is_more),
                        EndStep
                    ]
                }
            ],
            MainOperation.DownLiked: [
                (InputStep, StrOnlyInfo, bool),
                (SetFieldStep, DataFieldName.info_only),
                EndStep
            ],
            MainOperation.DownOne: [
                (InputStep, StrActorName, str),
                (SetFieldStep, DataFieldName.actor_name),
                EndStep
            ],
            MainOperation.LikeAll: [EndStep]
        }
    ]

    first_step = buildStep(step_json)
    input_data = {}
    first_step.execute(input_data)
    onStepsEnd(input_data)
