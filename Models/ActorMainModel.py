from sqlalchemy import String, event
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from Configs import DB_STR_LEN_REMARK
from Models.BaseModel import BaseModel
from Utils import PyUtil


class ActorMainModel(BaseModel):
    __tablename__ = "tab_actor_main"

    main_actor_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False)
    has_remark: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True)
    remark: Mapped[str] = mapped_column(
        String(DB_STR_LEN_REMARK), nullable=True, default=None)
    score: Mapped[int] = mapped_column(default=0)

    @validates("remark")
    def validate_remark(self, key, remark):
        remark = PyUtil.stripToNone(remark)
        if remark is not None and len(remark) > DB_STR_LEN_REMARK:
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
            'remark': PyUtil.encodeBase64(self.remark or "")
        }
        return json_data


@event.listens_for(ActorMainModel, 'before_insert')
@event.listens_for(ActorMainModel, 'before_update')
def update_has_remark(mapper, connection, target):
    target.has_remark = target.remark is not None
