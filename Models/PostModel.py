from sqlalchemy import String, ForeignKey, BigInteger
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Configs import DB_STR_LEN_LONG
from Models.BaseModel import BaseModel


class PostModel(BaseModel):
    __tablename__ = "tab_post"

    post_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id", ondelete="CASCADE"))
    is_dm: Mapped[bool] = mapped_column(default=False)
    completed: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(String(DB_STR_LEN_LONG))

    actor: Mapped["ActorModel"] = relationship(
        back_populates="post_list",
        cascade="all",
        passive_deletes=True
    )
    res_list: Mapped[list["ResModel"]] = relationship(
        back_populates="post",
        order_by="ResModel.res_index",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def toJson(self):
        return {
            # large number may be corrupted in js, so use string instead
            'post_id': str(self.post_id),
            'comment': self.comment
        }

    def __repr__(self) -> str:
        return f"Post(post_id={self.post_id!r}, actor_name={self.actor.actor_name})"
