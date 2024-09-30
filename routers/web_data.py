import json
from enum import Enum

from pydantic import BaseModel


class SortType(Enum):
    Default = 0
    Score = 1
    TotalPostCount = 2
    CategoryTime = 3


class ActorConditionForm(BaseModel):
    name: str
    group_id_list: list[int]
    tag_list: list[int]
    no_tag: bool
    min_score: int
    max_score: int
    sort_type: SortType
    sort_asc: bool
    remark_str: str
    remark_any: bool


class PostConditionForm(BaseModel):
    actor_id: int
    post_id_prefix: str
    has_comment: bool


class ServerData:
    def toJson(self):
        return self.__dict__


class ActorPostInfo(ServerData):
    actor_id: int
    actor_name: str
    post_count: int


class PostCommentForm(BaseModel):
    # large number may be corrupted in js, so use string instead
    post_id: str
    comment: str


class ActorTagForm(BaseModel):
    tag_name: str
    tag_priority: int


class BatchActorOperation(BaseModel):
    actor_ids: list[str]


class BatchActorGroup(BatchActorOperation):
    group_id: int


class ActorTagPriority(BaseModel):
    tag_id: int
    tag_priority: int


class AllActorTagPriorities(BaseModel):
    tag_priorities: list[ActorTagPriority]


class DownloadLimitForm(BaseModel):
    actor_count: int
    post_count: int
    post_filter: int
    file_size: int
    total_file_size: int
    allow_video: bool
    allow_img: bool


class ActorGroupForm(BaseModel):
    group_id: int
    group_name: str
    group_desc: str
    group_color: str
    has_folder: bool
    group_priority: int


class BaseDownloadForm(BaseModel):
    download_limit: DownloadLimitForm


class ActorIdDownloadForm(BaseDownloadForm):
    actor_ids: list[int]


class GroupDownloadForm(BaseDownloadForm):
    actor_group_id: int


class ActorUrl(BaseModel):
    actor_name: str
    full_url: str


class UrlDownloadForm(GroupDownloadForm):
    urls: list[ActorUrl]
