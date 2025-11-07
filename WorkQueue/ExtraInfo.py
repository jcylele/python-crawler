# extra information attached to queue items
# use composite pattern instead of inheritance
from Consts import QueueType, ResType
from Models.ModelInfos import ActorInfo


class BaseExtraInfo(object):
    def __init__(self):
        super().__init__()

    def queueType(self) -> QueueType:
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


class ResInfoExtraInfo(BaseExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's fetching the size of a resource
    """

    def __init__(self, actor_info: ActorInfo, post_id: int, res_id: int, res_type: ResType):
        super().__init__()
        self.actor_info = actor_info
        self.post_id = post_id
        self.res_id = res_id
        self.res_type = res_type

    def queueType(self):
        return QueueType.ResInfo

    def priority(self):
        # resources of newer post, larger post_id, higher priority
        if self.res_type == ResType.Video:
            return 1
        else:
            return 2

    def __repr__(self) -> str:
        return f"({self.res_id} of {self.post_id} of {self.actor_info.actor_name})"


class ResFileExtraInfo(ResInfoExtraInfo):
    """
    attached to UrlQueueItem, indicate that it's downloading a resource
    """

    def __init__(self, extra: ResInfoExtraInfo, file_path: str, file_size: int):
        super().__init__(extra.actor_info, extra.post_id, extra.res_id, extra.res_type)
        self.file_path = file_path
        self.file_size = file_size

    def queueType(self):
        return QueueType.FileDownload

    def priority(self):
        # small files first
        return self.file_size

    def __repr__(self) -> str:
        return f"(file {self.res_id} of {self.post_id} of {self.actor_info.actor_name})"
