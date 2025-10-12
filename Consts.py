from enum import Enum, auto, IntEnum


class CacheFile(Enum):
    CustomPage = 'configs/cache.json'
    Settings = 'configs/settings.json'


class CacheKey(Enum):
    # CustomPage
    CustomPage = 'Custom Page'
    # Settings
    DbConnectString = 'DbConnectString'
    RootUrl = 'RootUrl'
    ServerPort = 'ServerPort'
    RootFolder = 'RootFolder'
    ShowBrowser = 'ShowBrowser'


class GroupCondType(Enum):
    MinScore = 0  # param: score
    MaxScore = 1  # param: score
    HasAnyTag = 2  # param: bool
    Linked = 3  # param: bool


class NoticeType(Enum):
    All = 0
    UnlinkedActor = 1  # 2 actors are not linked, but share the same post
    InvalidPost = 2  # a post is invalid
    SameActorName = 3  # same name, different platform
    HasLinkedAccount = 4  # actor has linked accounts
    SimilarActorName = 5  # actor name is similar


class ActorLogType(Enum):
    Add = 1
    Group = 2
    Score = 3
    Tag = 4
    ResetPost = 5
    Remark = 6
    Link = 7
    Unlink = 8
    PostCount = 9
    ClearFolder = 10
    Comment = 11


class ResType(Enum):
    Image = 1
    Video = 2


class ResState(Enum):
    Init = 1
    Down = 2
    Skip = 3  # obsolete but keep for compatibility
    Del = 4


class WorkerType(Enum):
    """
    worker type, find corresponding worker classes in WorkerMgr.py
    """
    FileDown = auto()
    ResInfo = auto()
    ResValid = auto()

    FetchActors = auto()
    FetchActor = auto()
    FetchActorLink = auto()
    FetchPost = auto()


class QueueType(IntEnum):
    ResValid = auto()

    FetchActors = auto()
    FetchActor = auto()
    FetchActorLink = auto()
    
    # above queues are FIFO queues, below are priority queues
    MinPriorityQueue = 100

    FetchPost = auto()
    FileDownload = auto()
    ResInfo = auto()


class PostFilter(IntEnum):
    All = 0
    Normal = 1
    Current = 2
    Completed = 3


class TaskType(IntEnum):
    Default = 0
    Specific = 1
    Resume = 2

    MaxSingleActor = 100  # above are single actor tasks, below are multiple actor tasks

    New = 101
    Url = 102
    Group = 103
    FixPost = 104
    Manual = 105


class BoolEnum(Enum):
    ALL = auto()
    TRUE = auto()
    FALSE = auto()


class SortType(Enum):
    Default = 0
    Score = auto()
    CategoryTime = auto()
    TotalPostCount = auto()
    CompletedPostCount = auto()
    InitFileSize = auto()
    DownFileSize = auto()
    TotalFileSize = auto()
    LastPostFetchTime = auto()
    LastResDownloadTime = auto()


class ErrorCode(IntEnum):
    Success = 0

    Unavailable = 1

    MainActorNotFound = 101
    ActorNotFound = 102
    ActorGroupNotFound = 103
    TagNotFound = 104
    TagGroupNotFound = 105
    FolderNotFound = 106

    MultiLinkGroups = 201
    NotAllLinkedActors = 202
    UnlinkedActor = 203

    GroupAlreadyIn = 301
    GroupCondFailed = 302
    GroupHasActors = 303

    TagInOtherGroup = 401
    TagNotInGroup = 402
