from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Models.BaseModel import BaseModel


class ActorTagRelationship(BaseModel):
    __tablename__ = "rel_actor_tag"

    main_actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_main.main_actor_id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_tag.tag_id", ondelete="CASCADE"),
        primary_key=True
    )

    main_actor: Mapped["ActorMainModel"] = relationship(
        back_populates="rel_tags",
        cascade="all",
        passive_deletes=True
    )

    tag: Mapped["ActorTagModel"] = relationship(
        back_populates="rel_tags",
        cascade="all",
        passive_deletes=True
    )
