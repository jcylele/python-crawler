from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped

from Consts import ActorLogType
from Models.BaseModel import BaseModel, IntEnum


class ActorLogModel(BaseModel):
    __tablename__ = "tab_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id", ondelete="CASCADE"),
        index=True,
    )
    log_type: Mapped[ActorLogType] = mapped_column(IntEnum(ActorLogType))
    log_param: Mapped[str] = mapped_column(String(100), default="")
    log_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now())

    def toJson(self):
        json_data = {
            'log_type': self.log_type,
            'log_param': self.log_param,
        }

        return json_data
