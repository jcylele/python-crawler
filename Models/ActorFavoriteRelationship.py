from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Models.BaseModel import BaseModel


class ActorFavoriteRelationship(BaseModel):
    __tablename__ = "rel_actor_favorite"

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id", ondelete="CASCADE"),
        primary_key=True
    )

    folder_id: Mapped[int] = mapped_column(
        ForeignKey("tab_favorite_folder.folder_id", ondelete="CASCADE"),
        primary_key=True
    )

    folder_order: Mapped[int] = mapped_column(default=0)

    actor: Mapped["ActorModel"] = relationship(
        back_populates="rel_folders",
        cascade="all",
        passive_deletes=True
    )

    folder: Mapped["FavoriteFolderModel"] = relationship(
        back_populates="rel_actors",
        cascade="all",
        passive_deletes=True
    )