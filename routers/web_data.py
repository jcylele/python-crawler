from enum import Enum, auto
from typing import TypedDict

from pydantic import BaseModel

from Consts import ResType


class BoolEnum(Enum):
    ALL = auto()
    TRUE = auto()
    FALSE = auto()


class TagUsedInfo(TypedDict):
    used_count: int
    avg_score: float


class SortType(Enum):
    Default = 0
    Score = auto()
    CategoryTime = auto()
    TotalPostCount = auto()
    CurPostCount = auto()
    DownFileSize = auto()
    CurFileSize = auto()
    TotalFileSize = auto()

class SortItem(BaseModel):
    sort_type: SortType
    sort_asc: bool


class TagFilter(BaseModel):
    no_tag: bool
    must_have: list[int]
    any_of: list[list[int]]
    must_not_have: list[int]


class ActorConditionForm(BaseModel):
    name: str
    linked: bool
    group_id_list: list[int]
    folder_id: int
    tag_filter: TagFilter
    min_score: int
    max_score: int
    has_remark: BoolEnum
    remark_str: str

    sort_items: list[SortItem]


class PostFilterForm(BaseModel):
    actor_id: int
    post_id_prefix: str
    has_comment: bool
    comment: str


class ServerData(object):
    def toJson(self):
        return self.__dict__

class ResFileInfo(ServerData):
    file_path: str
    file_size: int
    res_size: int

    def __init__(self, file_path: str, file_size: int, res_size: int):
        self.file_path = file_path
        self.file_size = file_size
        self.res_size = res_size

class ActorVideoInfo(ServerData):
    is_landscape: bool
    duration: int
    file_count: int
    file_size: int

    def __init__(self, is_landscape: bool):
        self.is_landscape = is_landscape
        self.duration = 0
        self.file_count = 0
        self.file_size = 0

    def add_info(self, duration: float, file_size: int):
        self.duration += duration
        self.file_count += 1
        self.file_size += file_size


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


class CommonPriority(BaseModel):
    id: int
    priority: int


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

    @staticmethod
    def resumeVideoLimit():
        return DownloadLimitForm(actor_count=0, post_count=0, post_filter=0, res_type=ResType.Video.value, file_count=0, total_file_size=0, single_file_size=0)

    def toJson(self):
        return self.__dict__


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
    start_page: int


class ActorUrl(BaseModel):
    actor_name: str
    full_url: str


class UrlDownloadForm(GroupDownloadForm):
    urls: list[ActorUrl]

class CommonGroupForm(BaseModel):
    name: str
    desc: str
    priority: int

class ActorGroupForm(CommonGroupForm):
    group_color: str
    has_folder: bool