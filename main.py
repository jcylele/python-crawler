import Configs
import Consts
import LogUtil
import Steps.Entrance as Entrance
from Models.BaseModel import ActorTag
from Steps.DataInputSteps import MainOperation


def enter():
    """
    original start point
    :return:
    """
    Entrance.initEnv()
    for tip in MainOperation.formatMainOperationTip():
        LogUtil.info(tip)
    op = input()
    eop = MainOperation(int(op))
    if eop == MainOperation.DownLiked:
        is_all = input(Entrance.StrOnlyInfo)
        if is_all == 'y':
            Entrance.setConfig(Configs.ConfigType.All)
            Entrance.setWorkerCount(Consts.WorkerType.FileDown, 0)
        elif is_all == 'n':
            Entrance.setConfig(Configs.ConfigType.Liked)
        else:
            raise Exception(f"invalid option {is_all}")
        Entrance.downloadByActorTag(ActorTag.Liked)
    elif eop == MainOperation.DownSample:
        is_new = input(Entrance.StrNewActors)
        if is_new == 'y':
            Entrance.setConfig(Configs.ConfigType.Sample)
            Entrance.downloadNewActors()
        elif is_new == 'n':
            is_more = input(Entrance.StrMoreSample)
            if is_more == 'y':
                Entrance.setConfig(Configs.ConfigType.Liked)
            elif is_more == 'n':
                Entrance.setConfig(Configs.ConfigType.Sample)
            else:
                raise Exception(f"invalid option {is_more}")
            Entrance.downloadByActorTag(ActorTag.Init)
        else:
            raise Exception(f"invalid option {is_new}")
    elif eop == MainOperation.DownOne:
        actor_name = input(Entrance.StrActorName)
        Configs.setConfig(Configs.ConfigType.All)
        Entrance.downloadActor(actor_name)
    elif eop == MainOperation.LikeAll:
        Entrance.likeAllActors()
    else:
        LogUtil.error("Wrong Operation")


if __name__ == '__main__':
    if False:
        enter()
    else:
        Entrance.enter()

