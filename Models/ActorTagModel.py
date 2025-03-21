from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Models.BaseModel import BaseModel


class ActorTagModel(BaseModel):
    __tablename__ = "tab_actor_tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(30))
    tag_priority: Mapped[int] = mapped_column(default=0)

    rel_tags: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
