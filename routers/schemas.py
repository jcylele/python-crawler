# schemas of models for response

from pydantic import BaseModel, field_validator, computed_field, model_validator

from Consts import ActorLogType, DateFormat, GroupCondType, NoticeType, ResState
from Ctrls import PathCtrl, RequestCtrl
from Models.ActorModel import ActorModel
from Utils import PyUtil


class PostResponse(BaseModel):
    post_id: str
    comment: str | None = None

    @field_validator('post_id', mode='before')
    @classmethod
    def post_id_to_str(cls, v):
        return str(v)

    @field_validator('comment', mode='before')
    @classmethod
    def comment_to_str(cls, v):
        return v or ""

    class Config:
        from_attributes = True


class NoticeResponse(BaseModel):
    notice_id: int
    notice_type: NoticeType
    notice_param0: str
    notice_param1: str
    notice_param2: str
    notice_param3: str

    class Config:
        from_attributes = True


class ActorLogResponse(BaseModel):
    log_type: ActorLogType
    log_param: str
    log_time: str

    @field_validator('log_time', mode='before')
    @classmethod
    def log_time_to_str(cls, v):
        return PyUtil.datetime_format(v, DateFormat.Full)

    class Config:
        from_attributes = True


class ActorGroupCondResponse(BaseModel):
    cond_type: GroupCondType
    cond_param: int

    class Config:
        from_attributes = True


class ActorGroupResponse(BaseModel):
    # original fields
    group_id: int
    group_name: str
    group_desc: str
    group_color: str
    flags: int
    group_priority: int

    # properties from ORM
    cond_list: list[ActorGroupCondResponse]

    class Config:
        from_attributes = True


class ActorFileInfoResponse(BaseModel):
    actor_id: int
    res_state: ResState
    img_size: int
    video_size: int
    img_count: int
    video_count: int

    class Config:
        from_attributes = True


class ActorTagResponse(BaseModel):
    tag_id: int
    tag_name: str
    tag_priority: int
    tag_group_id: int

    # use field_validator to handle None value
    @field_validator('tag_group_id', mode='before')
    @classmethod
    def null_to_0(cls, v):
        return v or 0

    class Config:
        from_attributes = True


class ActorTagFullResponse(ActorTagResponse):
    used_count: int = 0
    avg_score: float = 0


class ActorTagGroupResponse(BaseModel):
    group_id: int
    group_name: str
    group_desc: str
    group_priority: int

    class Config:
        from_attributes = True


class FavoriteFolderResponse(BaseModel):
    folder_id: int
    folder_name: str
    folder_desc: str
    folder_priority: int

    class Config:
        from_attributes = True


class ActorResponse(BaseModel):
    # original fields

    actor_id: int
    actor_name: str
    actor_platform: str
    actor_link: str  # need this to calculate href
    actor_group_id: int
    comment: str | None = None  # may be None

    # properties from ORM

    is_linked: bool
    has_last_post_id: bool
    folder_ids: list[int]
    commented_posts: list[PostResponse]

    # properties from main actor

    score: int
    remark: str | None = None
    tag_ids: list[int] = []

    # use field_validator to handle None value
    @field_validator('comment', mode='before')
    @classmethod
    def comment_to_str(cls, v):
        return v or ""

    @field_validator('remark', mode='before')
    @classmethod
    def remark_to_str(cls, v):
        return v or ""

    # computed_fields
    @computed_field
    @property
    def icon(self) -> str:
        return PathCtrl.smartActorIconSrc(self)

    @computed_field
    @property
    def href(self) -> str:
        return RequestCtrl.formatActorHref(self)

    class Config:
        from_attributes = True
