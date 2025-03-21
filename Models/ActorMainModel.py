from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Models.BaseModel import BaseModel
from Utils import PyUtil


class ActorMainModel(BaseModel):
    __tablename__ = "tab_actor_main"

    main_actor_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False)
    remark: Mapped[str] = mapped_column(String(100), default="")
    score: Mapped[int] = mapped_column(default=0)
    rel_tags: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="main_actor",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def toJson(self):
        json_data = {
            'score': self.score,
            'tag_ids': [tag.tag_id for tag in self.rel_tags],
            'remark': PyUtil.encodeBase64(self.remark)
        }
        return json_data
