

from pydantic import BaseModel

from Consts import BoolEnum, ResType, SortType


class TagUsedInfo(BaseModel):
    used_count: int
    avg_score: float


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
    has_comment: BoolEnum
    comment_str: str
    post_completed: BoolEnum
    res_completed: BoolEnum

    sort_items: list[SortItem]


class PostFilterForm(BaseModel):
    actor_id: int
    post_id_prefix: str
    has_comment: bool
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


class CommonPriority(BaseModel):
    id: int
    priority: int


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

    @staticmethod
    def fixPostsLimit():
        return DownloadLimitForm(actor_count=0, post_count=0, post_filter=0, res_type=ResType.Video.value, file_count=0, total_file_size=0, single_file_size=1)

    @staticmethod
    def fixResLimit():
        return DownloadLimitForm(actor_count=0, post_count=0, post_filter=0, res_type=ResType.Video.value, file_count=0, total_file_size=0, single_file_size=1)


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
    flags: int


class GroupTimeStatsForm(BaseModel):
    start_date: str
    end_date: str
    group_ids: list[int]
