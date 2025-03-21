from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Consts import GroupCondType
from Models.BaseModel import BaseModel, IntEnum


class ActorGroupCondModel(BaseModel):
    __tablename__ = "tab_actor_group_condition"

    cond_id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey(
        "tab_actor_group.group_id", ondelete="CASCADE"))
    cond_type: Mapped[GroupCondType] = mapped_column(IntEnum(GroupCondType))
    cond_param: Mapped[int] = mapped_column(default=0)

    group: Mapped["ActorGroupModel"] = relationship(
        back_populates="cond_list",
        cascade="all",
        passive_deletes=True
    )

    def toJson(self):
        json_data = {
            'cond_type': self.cond_type,
            'cond_param': self.cond_param
        }

        return json_data
