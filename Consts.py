from enum import Enum, IntFlag, auto, IntEnum


class DateFormat(Enum):
    Time = '%H:%M:%S'
    Date = '%Y-%m-%d'
    MonthDay = '%m-%d'
    Full = '%Y-%m-%d %H:%M:%S'


class CacheFile(Enum):
    CustomPage = 'configs/cache.json'
    Settings = 'configs/settings.json'
    LastRunTime = 'configs/last_run_time.json'
    SimilarConfigs = 'configs/similar_configs.json'


class CacheKey(Enum):
    # CustomPage
    CustomPage = 'Custom Page'
    # Settings
    DbConnectString = 'DbConnectString'
    RootUrl = 'RootUrl'
    ServerPort = 'ServerPort'
    RootFolder = 'RootFolder'
    ShowBrowser = 'ShowBrowser'
    # SimilarConfigs
    SimilarIconThreshold = 'similar_icon_threshold'
    SimilarMinSubstringLen = 'min_substring_len'
    SimilarMinPureNameLen = 'min_pure_name_len'
    SimilarNameSubstringSkip = 'similar_name_substring_skip'
    SimilarNamePreFix = 'similar_name_pre_fix'
    SimilarNamePostFix = 'similar_name_post_fix'
    SimilarSpSplitChars = 'sp_split_chars'
    SimilarSpLastChars = 'sp_last_chars'


class GroupCondType(Enum):
    MinScore = 0  # param: score
    MaxScore = 1  # param: score
    HasAnyTag = 2  # param: bool
    Linked = 3  # param: bool
    HasRemark = 4  # param: bool


class NoticeType(Enum):
    All = 0
    UnlinkedActor = 1  # 2 actors are not linked, but share the same post
    InvalidPost = 2  # a post is invalid
    SameActorName = 3  # same name, different platform
    HasLinkedAccount = 4  # actor has linked accounts
    SimilarActorName = 5  # actor name is similar
    SimilarIcon = 6  # icon is similar


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
    Null = 0
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
    FetchPost = auto()

    # above queues are FIFO queues, below are priority queues
    MinPriorityQueue = 100

    FileDownload = auto()
    ResInfo = auto()


class PostFilter(IntEnum):
    All = 0
    Normal = 1
    Current = 2
    Completed = 3


class TaskType(IntEnum):
    Default = 0
    Specific = auto()
    Resume = auto()
    FixPost = auto()
    FixRes = auto()

    MaxSingleActor = 100  # above are single actor tasks, below are multiple actor tasks

    New = auto()
    Url = auto()
    Group = auto()
    Manual = auto()


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
    FavoriteCount = auto()


class EActorGroupFlag(IntFlag):
    """
    actor group flag, used to store actor group boolean properties
    """
    HasFolder = 1
    IsInitial = 1 << 1
    ShowVideoInfo = 1 << 2


class EFixFilter(IntFlag):
    Overflow = 1  # current post count > total post count
    TotalZero = 1 << 1  # total post count = 0
    LinkNotChecked = 1 << 2  # link not checked
    IconNotExists = 1 << 3  # icon not exists
    MissingPosts = 1 << 4  # actor has missing posts
    NoFavorite = 1 << 5  # actor has no favorite count


class ErrorCode(IntEnum):
    Success = 0

    Unavailable = 1
    ServerError = 2

    MainActorNotFound = 101
    ActorNotFound = 102
    ActorGroupNotFound = 103
    TagNotFound = 104
    TagGroupNotFound = 105
    FolderNotFound = 106
    ResNotFound = 107
    PostNotFound = 108

    MultiLinkGroups = 201
    NotAllLinkedActors = 202
    UnlinkedActor = 203
    NoNewMainActor = 204

    GroupAlreadyIn = 301
    GroupCondFailed = 302
    GroupHasActors = 303

    TagInOtherGroup = 401
    TagNotInGroup = 402
    TagInGroup = 403

    BatchFileInfoTooLarge = 501
