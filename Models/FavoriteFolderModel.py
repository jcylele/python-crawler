from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from Configs import DB_STR_LEN_LONG, DB_STR_LEN_SHORT
from Models.BaseModel import BaseModel


class FavoriteFolderModel(BaseModel):
    __tablename__ = "tab_favorite_folder"

    folder_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True)
    folder_name: Mapped[str] = mapped_column(
        String(DB_STR_LEN_SHORT), unique=True)
    folder_desc: Mapped[str] = mapped_column(String(DB_STR_LEN_LONG))

    rel_actors: Mapped[list["ActorFavoriteRelationship"]] = relationship(
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    @validates("folder_name")
    def validate_folder_name(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_SHORT)

    @validates("folder_desc")
    def validate_folder_desc(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_LONG)

    def toJson(self):
        return {
            "folder_id": self.folder_id,
            "folder_name": self.folder_name,
            "folder_desc": self.folder_desc
        }
