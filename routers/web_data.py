from enum import Enum
from typing import TypedDict
from pydantic import BaseModel


class TagUsedInfo(TypedDict):
    used_count: int
    avg_score: float


class SortType(Enum):
    Default = 0
    Score = 1
    TotalPostCount = 2
    CategoryTime = 3


class SortItem(BaseModel):
    sort_type: SortType
    sort_asc: bool


class ActorConditionForm(BaseModel):
    name: str
    linked: bool
    group_id_list: list[int]
    tag_list: list[int]
    no_tag: bool
    min_score: int
    max_score: int
    remark_str: str
    remark_any: bool

    sort_items: list[SortItem]


class PostConditionForm(BaseModel):
    actor_id: int
    post_id_prefix: str
    has_comment: bool


class ServerData(object):
    def toJson(self):
        return self.__dict__


class ActorPostInfo(ServerData):
    actor_id: int
    actor_name: str
    post_count: int


class BaseResult(ServerData):
    succeed: bool
    msg: str

    def __init__(self, succeed: bool, msg: str):
        self.succeed = succeed
        self.msg = msg


class ActorResult(BaseResult):
    actor: "ActorModel"

    def __init__(self, succeed: bool, msg: str, actor: "ActorModel" = None):
        super().__init__(succeed, msg)
        self.actor = actor


class ActorListResult(BaseResult):
    actor_list: list["ActorModel"]

    def __init__(self, succeed: bool, msg: str, actor_list: list["ActorModel"] = []):
        super().__init__(succeed, msg)
        self.actor_list = actor_list


class PostCommentForm(BaseModel):
    # large number may be corrupted in js, so use string instead
    post_id: str
    comment: str


class ActorTagForm(BaseModel):
    tag_name: str
    tag_priority: int


class BatchActorGroup(BaseModel):
    actor_ids: list[int]
    group_id: int


class LinkActorForm(BaseModel):
    actor_ids: list[int]
    score: int
    tag_list: list[int]
    remark: str


class ActorTagPriority(BaseModel):
    tag_id: int
    tag_priority: int


class AllActorTagPriorities(BaseModel):
    tag_priorities: list[ActorTagPriority]


class DownloadProgress(ServerData):
    actor_count = 0
    file_count = 0
    total_file_size = 0

    def __init__(self):
        super().__init__()
        self.actor_count = 0
        self.file_count = 0
        self.total_file_size = 0


class DownloadLimitForm(BaseModel):
    actor_count: int
    # post count of each actor
    post_count: int
    post_filter: int
    # res limit
    res_type: int
    file_count: int
    total_file_size: int
    single_file_size: int

    def toJson(self):
        return self.__dict__


class ActorGroupForm(BaseModel):
    group_id: int
    group_name: str
    group_desc: str
    group_color: str
    has_folder: bool
    group_priority: int


class ActorGroupCond(BaseModel):
    cond_type: int
    cond_param: int


class BaseDownloadForm(BaseModel):
    download_limit: DownloadLimitForm


class ActorIdDownloadForm(BaseDownloadForm):
    actor_ids: list[int]


class GroupDownloadForm(BaseDownloadForm):
    actor_group_id: int


class NewDownloadForm(GroupDownloadForm):
    from_start: bool


class ActorUrl(BaseModel):
    actor_name: str
    full_url: str


class UrlDownloadForm(GroupDownloadForm):
    urls: list[ActorUrl]
