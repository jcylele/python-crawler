from sqlalchemy import select, update
from sqlalchemy.orm import Session

from Consts import ActorLogType
from Models.ActorLogModel import ActorLogModel
from Models.ActorModel import ActorModel


def getActorLogs(session: Session, actor_id: int) -> list[ActorLogModel]:
    stmt = (select(ActorLogModel)
            .where(ActorLogModel.actor_id == actor_id)
            .order_by(ActorLogModel.log_id))
    return list(session.scalars(stmt))


def addActorLog(session: Session, actor_id: int, log_type: ActorLogType, *params):
    alm = ActorLogModel()
    alm.actor_id = actor_id
    alm.log_type = log_type
    alm.log_param = "\n".join(map(str, params))

    session.add(alm)
    session.flush()

    stmt = (update(ActorModel)
            .where(ActorModel.actor_id == actor_id)
            .values(last_log_time=alm.log_time))
    session.execute(stmt)

    return alm
