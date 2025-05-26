from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from Consts import ResState
from Models.BaseModel import BaseModel, IntEnum


class ActorFileInfoModel(BaseModel):
    __tablename__ = "tab_actor_file_info"

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id", ondelete="CASCADE"),
        primary_key=True
    )
    res_state: Mapped[ResState] = mapped_column(
        IntEnum(ResState), nullable=False, primary_key=True
    )
    res_size: Mapped[int] = mapped_column(BigInteger)
    img_count: Mapped[int] = mapped_column()
    video_count: Mapped[int] = mapped_column()

    def toJson(self):
        return {
            "actor_id": self.actor_id,
            "res_state": self.res_state.value,
            "res_size": self.res_size,
            "img_count": self.img_count,
            "video_count": self.video_count
        }
