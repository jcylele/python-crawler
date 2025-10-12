from typing import Generic, TypeAlias, TypeVar
from pydantic import BaseModel
from Consts import CacheKey, ErrorCode, TaskType
from routers.schemas import ActorFileInfoResponse
from routers.web_data import DownloadLimitForm

T = TypeVar('T')


class UnifiedResponse(BaseModel, Generic[T]):
    error_code: ErrorCode = ErrorCode.Success
    data: T | None = None


UnifiedListResponse: TypeAlias = UnifiedResponse[list[T]]
CommonResponse: TypeAlias = UnifiedResponse[None]


class DownloadProgress(BaseModel):
    actor_count: int = 0
    file_count: int = 0
    total_file_size: int = 0


class DownloadLimitResponse(BaseModel):
    limit: DownloadLimitForm
    progress: DownloadProgress


class ResSizeCount(BaseModel):
    min: int = 0
    max: int = 0
    count_map: dict[int, int] = {}


class ResFileInfo(BaseModel):
    file_path: str
    file_size: int
    res_size: int


class ActorVideoInfo(BaseModel):
    is_landscape: bool
    duration: int = 0
    file_count: int = 0
    file_size: int = 0

    def add_info(self, duration: int, file_size: int):
        self.duration += duration
        self.file_count += 1
        self.file_size += file_size


class DownloadingVideoStats(BaseModel):
    actor_id: int
    actor_name: str
    file_count: int = 0
    file_size: int = 0
    res_size: int = 0

    def add_info(self, file_size: int, res_size: int):
        self.file_count += 1
        self.file_size += file_size
        self.res_size += res_size


class ActorPostInfo(BaseModel):
    actor_id: int
    actor_name: str
    post_count: int


class ActorFileDetail(BaseModel):
    thumbnail_count: int
    res_info: list[ActorFileInfoResponse]
    total_post_count: int
    unfinished_post_count: int
    finished_post_count: int
    is_completed: bool


class NoticeCount(BaseModel):
    notice_type: int
    count: int


class TagCount(BaseModel):
    tag_id: int
    count: int


class CommentCount(BaseModel):
    comment: str
    count: int

class ActorAbstract(BaseModel):
    actor_id: int
    actor_name: str
    actor_group_id: int


class DownloadTaskResponse(BaseModel):
    uid: int
    type: TaskType
    arg: int
    download_limit: DownloadLimitResponse
    worker_count: dict[str, int]
    queue_count: dict[str, int]
    actor_abstract: ActorAbstract|None = None


class Settings(BaseModel):
    DbConnectString: str
    RootUrl: str
    ServerPort: int
    RootFolder: str
    ShowBrowser: bool


class SettingItem(BaseModel):
    key: CacheKey
    value: str|int|bool
