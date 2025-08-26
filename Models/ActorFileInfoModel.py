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
    # res_size: Mapped[int] = mapped_column(BigInteger)
    img_size: Mapped[int] = mapped_column(BigInteger)
    video_size: Mapped[int] = mapped_column(BigInteger)
    img_count: Mapped[int] = mapped_column()
    video_count: Mapped[int] = mapped_column()

    def equal(self, other: 'ActorFileInfoModel') -> bool:
        return self.img_size == other.img_size and \
            self.video_size == other.video_size and \
            self.img_count == other.img_count and \
            self.video_count == other.video_count

