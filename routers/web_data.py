from enum import Enum

from pydantic import BaseModel


class SortType(Enum):
    Default = 0
    Score = 1
    TotalPostCount = 2


class ActorConditionForm(BaseModel):
    name: str
    category_list: list[int]
    tag_list: list[int]
    no_tag: bool
    min_score: int
    max_score: int
    sort_type: SortType
    sort_asc: bool
    remark_str: str
    remark_any: bool


class PostConditionForm(BaseModel):
    actor_name: str
    post_id_prefix: str
    has_comment: bool


class PostCommentForm(BaseModel):
    post_id: int
    comment: str


class ActorTagForm(BaseModel):
    tag_name: str
    tag_priority: int


class BatchActorOperation(BaseModel):
    actor_names: list[str]


class BatchActorCategory(BatchActorOperation):
    category: int


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


class NameDownloadForm(BaseDownloadForm):
    actor_names: list[str]


class CategoryDownloadForm(BaseDownloadForm):
    actor_category: int


class ActorUrl(BaseModel):
    actor_name: str
    full_url: str


class UrlDownloadForm(CategoryDownloadForm):
    urls: list[ActorUrl]
