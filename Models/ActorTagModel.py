from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Configs import DB_STR_LEN_SHORT
from Models.BaseModel import BaseModel


class ActorTagModel(BaseModel):
    __tablename__ = "tab_actor_tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    tag_priority: Mapped[int] = mapped_column(default=0)

    rel_main_actors: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
