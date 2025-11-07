from sqlalchemy import Index, String, ForeignKey, BigInteger, event, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_LONG, DB_STR_LEN_BIG_INT
from Models.BaseModel import BaseModel


class PostModel(BaseModel):
    __tablename__ = "tab_post"

    post_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False)
    post_id_str: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), nullable=False)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id", ondelete="CASCADE"))
    completed: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), nullable=True, default=None)
    has_comment: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )
    has_thumbnail: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )
    last_fetch_time: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # 在类定义后添加索引定义
    __table_args__ = (
        Index('idx_post_id_str', 'post_id_str',
              mysql_length=8),  # 使用 mysql_length 参数, 至少6位数字(DM开头)已经足够
    )

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

    @validates("comment")
    def validate_comment(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_LONG)

    def __repr__(self) -> str:
        return f"Post(post_id={self.post_id!r}, actor_name={self.actor.actor_name})"


@event.listens_for(PostModel, 'before_insert')
@event.listens_for(PostModel, 'before_update')
def update_post_id_str(mapper, connection, target):
    target.has_comment = target.comment is not None
