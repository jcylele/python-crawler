
from sqlalchemy import String, ForeignKey, DateTime, func, BigInteger, event
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_REMARK, DB_STR_LEN_SHORT
from Models.BaseModel import BaseModel
from Utils import PyUtil


class ActorModel(BaseModel):
    __tablename__ = "tab_actor"

    actor_id: Mapped[int] = mapped_column(primary_key=True)
    actor_name: Mapped[str] = mapped_column(
        String(DB_STR_LEN_SHORT), index=True)
    actor_group_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_group.group_id"))
    actor_platform: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    actor_link: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    total_post_count: Mapped[int] = mapped_column(default=0)
    current_post_count: Mapped[int] = mapped_column(default=0)
    completed_post_count: Mapped[int] = mapped_column(default=0)
    last_post_fetch_time: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_res_download_time: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    main_actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("tab_actor_main.main_actor_id"),
        nullable=True
    )
    group_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now())
    last_post_id: Mapped[int] = mapped_column(BigInteger, default=0)
    link_checked: Mapped[bool] = mapped_column(default=False)
    manual_done: Mapped[bool] = mapped_column(default=False)
    # info for this actor (not shared), just to record trivial things
    has_comment: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True)
    comment: Mapped[str] = mapped_column(
        String(DB_STR_LEN_REMARK), nullable=True, default=None)

    actor_group: Mapped["ActorGroupModel"] = relationship()
    main_actor: Mapped["ActorMainModel"] = relationship()
    post_list: Mapped[list["PostModel"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    rel_folders: Mapped[list["ActorFavoriteRelationship"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    @validates("comment")
    def validate_comment(self, key, comment):
        comment = PyUtil.stripToNone(comment)
        return self.truncate(key, comment, DB_STR_LEN_REMARK)

    def setGroup(self, group_id):
        if self.actor_group_id == group_id:
            return
        self.actor_group_id = group_id
        self.group_time = func.now()

    @property
    def commented_posts(self):
        return [post for post in self.post_list if post.comment]

    @property
    def folder_ids(self) -> list[int]:
        return [rel.folder_id for rel in self.rel_folders]

    @property
    def is_linked(self) -> bool:
        return self.main_actor_id != self.actor_id

    @property
    def score(self) -> int:
        return self.main_actor.score

    @property
    def remark(self) -> str:
        return self.main_actor.remark

    @property
    def tag_ids(self) -> list[int]:
        return self.main_actor.tag_ids


@event.listens_for(ActorModel, 'before_insert')
@event.listens_for(ActorModel, 'before_update')
def update_has_comment(mapper, connection, target):
    target.has_comment = target.comment is not None
