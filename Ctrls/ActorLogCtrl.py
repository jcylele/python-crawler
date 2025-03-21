from sqlalchemy.orm import Session

from Consts import ActorLogType
from Models.ActorLogModel import ActorLogModel


def getActorLogs(session: Session, actor_id: int):
    logs = (session.query(ActorLogModel)
            .filter(ActorLogModel.actor_id == actor_id)
            .order_by(ActorLogModel.log_id)
            .all())
    return [log for log in logs]


def addActorLog(session: Session, actor_id: int, log_type: ActorLogType, *params):
    alm = ActorLogModel()
    alm.actor_id = actor_id
    alm.log_type = log_type
    alm.log_param = "\n".join(map(str, params))

    session.add(alm)
    session.flush()
    return alm
