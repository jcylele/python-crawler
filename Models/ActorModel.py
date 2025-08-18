from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_REMARK, DB_STR_LEN_SHORT
from Ctrls import RequestCtrl
from Models.ActorInfo import ActorInfo
from Models.BaseModel import BaseModel
from Utils import PyUtil


class ActorModel(BaseModel):
    __tablename__ = "tab_actor"

    actor_id: Mapped[int] = mapped_column(primary_key=True)
    actor_name: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT), index=True)
    actor_group_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_group.group_id"))
    actor_platform: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    actor_link: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    total_post_count: Mapped[int] = mapped_column(default=0)
    current_post_count: Mapped[int] = mapped_column(default=0)
    completed_post_count: Mapped[int] = mapped_column(default=0)
    last_post_fetch_time: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_res_download_time: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    main_actor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tab_actor_main.main_actor_id"),
        nullable=True
    )
    group_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now())
    last_post_id: Mapped[int] = mapped_column(BigInteger, default=0)
    link_checked: Mapped[bool] = mapped_column(default=False)
    manual_done: Mapped[bool] = mapped_column(default=False)
    # info for this actor (not shared), just to record trivial things
    comment: Mapped[str] = mapped_column(String(DB_STR_LEN_REMARK), nullable=True, default=None)

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

    def isLinked(self):
        return self.main_actor_id != self.actor_id

    def setGroup(self, group_id):
        if self.actor_group_id == group_id:
            return
        self.actor_group_id = group_id
        self.group_time = func.now()

    def toJson(self):
        actor_info = ActorInfo(self)
        json_data = {
            'actor_id': self.actor_id,
            'actor_name': self.actor_name,
            'actor_platform': self.actor_platform,
            'actor_group_id': self.actor_group_id,
            'icon': RequestCtrl.smartActorIconSrc(actor_info),
            'href': RequestCtrl.formatActorHref(actor_info),
            'is_linked': self.isLinked(),
            'comment': self.comment or ""
        }
        # posts with comment
        commented_posts = [post.toJson()
                           for post in self.post_list if post.comment]
        json_data['commented_posts'] = commented_posts
        json_data['folder_ids'] = [rel_folder.folder_id for rel_folder in self.rel_folders]
        # flattened main_actor
        json_data.update(self.main_actor.toJson())
        return json_data

    def __repr__(self) -> str:
        return f"Actor(name={self.actor_name!r}, group={self.actor_group.group_name!r})"
