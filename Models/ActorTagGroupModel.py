from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_SHORT, DB_STR_LEN_LONG
from Models.BaseModel import BaseModel


class ActorTagGroupModel(BaseModel):
    __tablename__ = "tab_actor_tag_group"
    
    group_id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str] = mapped_column(String(DB_STR_LEN_SHORT))
    group_desc: Mapped[str] = mapped_column(String(DB_STR_LEN_LONG), nullable=True, default=None)
    group_priority: Mapped[int] = mapped_column(default=0)
    
    # 关联的标签列表
    tags: Mapped[list["ActorTagModel"]] = relationship(
        back_populates="tag_group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    @validates("group_name")
    def validate_group_name(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_SHORT)
    
    @validates("group_desc")
    def validate_group_desc(self, key, value):
        return self.truncate(key, value, DB_STR_LEN_LONG)
    
