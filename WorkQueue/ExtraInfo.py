# extra information attached to queue items
# use composite pattern instead of inheritance

from WorkQueue import QueueMgr


class BaseExtraInfo(object):
    def __init__(self):
        super().__init__()

    def queueType(self) -> QueueMgr.QueueType:
        """
        which queue should the attached item throw into
        :return:
        """
        raise NotImplementedError("subclasses of BaseExtraInfo must implement method queueType")

    def priority(self) -> int:
        """
        prioritize the attached item, smaller number represents higher priority
        :return:
        """
        raise NotImplementedError("subclasses of BaseExtraInfo must implement method priority")


class FilePathExtraInfo(BaseExtraInfo):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path


class ActorsExtraInfo(BaseExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's a page for lists of actors
    """
    def __init__(self, start_order: int = 0):
        super().__init__()
        self.start_order = start_order

    def queueType(self):
        return QueueMgr.QueueType.AnalyseActors

    def priority(self):
        # highest priority
        return 0

    def __repr__(self) -> str:
        return f"(actors?o={self.start_order})"


class ActorExtraInfo(BaseExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's a page for lists of posts of an actor
    """
    def __init__(self, actor_name: str, start_order: int = 0):
        super().__init__()
        self.actor_name = actor_name
        self.start_order = start_order

    def queueType(self):
        return QueueMgr.QueueType.AnalyseUser

    def priority(self):
        # smaller start_order, higher priority
        return 10000 + self.start_order

    def __repr__(self) -> str:
        return f"({self.actor_name}?o={self.start_order})"


class PostExtraInfo(BaseExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's a page for resources of a post
    """
    def __init__(self, actor_name: str, post_id: int):
        super().__init__()
        self.actor_name = actor_name
        self.post_id = post_id

    def queueType(self):
        return QueueMgr.QueueType.AnalysePost

    def priority(self):
        # newer post, larger post_id, higher priority
        return 20000 + 10000 - (self.post_id // 100000)

    def __repr__(self) -> str:
        return f"({self.post_id} of {self.actor_name})"


class ResInfoExtraInfo(BaseExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's fetching the size of a resource
    """
    def __init__(self, actor_name: str, post_id: int, res_id: int):
        super().__init__()
        self.actor_name = actor_name
        self.post_id = post_id
        self.res_id = res_id

    def queueType(self):
        return QueueMgr.QueueType.ResInfo

    def priority(self):
        # resources of newer post, larger post_id, higher priority
        return 10000 + 10000 - (self.post_id // 100000)

    def __repr__(self) -> str:
        return f"({self.res_id} of {self.post_id} of {self.actor_name})"


class ResFileExtraInfo(ResInfoExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's downloading a resource
    """
    def __init__(self, extra: ResInfoExtraInfo, file_path: str, file_size: int):
        super().__init__(extra.actor_name, extra.post_id, extra.res_id)
        self.file_path = file_path
        self.file_size = file_size

    def queueType(self):
        return QueueMgr.QueueType.FileDownload

    def priority(self):
        # small files first
        return self.file_size

    def __repr__(self) -> str:
        return f"(file {self.res_id} of {self.post_id} of {self.actor_name})"


