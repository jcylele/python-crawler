from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_SHORT
from Models.BaseModel import BaseModel


class ActorTagModel(BaseModel):
    __tablename__ = "tab_actor_tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    tag_priority: Mapped[int] = mapped_column(default=0)
    # 新增：标签组关联
    tag_group_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_tag_group.group_id", ondelete="SET NULL"),
        nullable=True,
        default=None
    )

    rel_main_actors: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

        # 新增：标签组关联
    tag_group: Mapped["ActorTagGroupModel"] = relationship(
        back_populates="tags",
        cascade="all",
        passive_deletes=True
    )

    @validates("tag_name")
    def validate_tag_name(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_SHORT)

