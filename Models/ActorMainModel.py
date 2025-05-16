from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_REMARK
from Models.BaseModel import BaseModel
from Utils import PyUtil


class ActorMainModel(BaseModel):
    __tablename__ = "tab_actor_main"

    main_actor_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False)
    remark: Mapped[str] = mapped_column(String(DB_STR_LEN_REMARK), default="")
    score: Mapped[int] = mapped_column(default=0)

    @validates("remark")
    def validate_remark(self, key, remark):
        if len(remark) > DB_STR_LEN_REMARK:
            remark = remark[:DB_STR_LEN_REMARK]
        return remark

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
