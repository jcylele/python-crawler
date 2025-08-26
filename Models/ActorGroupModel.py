from Models.ActorGroupCondModel import ActorGroupCondModel
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_SHORT, DB_STR_LEN_LONG, DB_STR_LEN_COLOR
from Models.BaseModel import BaseModel


class ActorGroupModel(BaseModel):
    __tablename__ = "tab_actor_group"

    group_id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    group_desc: Mapped[str] = mapped_column(String(DB_STR_LEN_LONG))
    group_color: Mapped[str] = mapped_column(String(DB_STR_LEN_COLOR))
    has_folder: Mapped[bool] = mapped_column(default=False)
    group_priority: Mapped[int] = mapped_column(default=0)

    group_cond_list: Mapped[list[ActorGroupCondModel]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    @validates("group_name")
    def validate_group_name(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_SHORT)

    @validates("group_desc")
    def validate_group_desc(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_LONG)

    @property
    def cond_list(self) -> list[ActorGroupCondModel]:
        return [cond for cond in self.group_cond_list]


