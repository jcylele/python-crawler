from turtle import pos
from Models.ModelInfos import ActorInfo, PostInfo
from WorkQueue.BaseQueueItem import BaseQueueItem


class FetchActorsQueueItem(BaseQueueItem):
    """
    fetch actor list
    """

    def __init__(self, start_page: int):
        super().__init__()
        self.start_page = start_page

    def __repr__(self):
        return f"FetchActorsQueueItem {self.start_page}"


class FetchActorQueueItem(BaseQueueItem):
    """
    fetch a single actor
    """

    def __init__(self, actor_id: int):
        super().__init__()
        self.actor_id = actor_id

    def __repr__(self):
        return f"FetchActorQueueItem({self.actor_id})"


class FetchPostQueueItem(BaseQueueItem):
    """
    fetch a single actor
    """

    def __init__(self, actor_info: ActorInfo, post_info: PostInfo):
        super().__init__()
        self.actor_info = actor_info
        self.post_id = post_info.post_id
        self.post_id_str = post_info.post_id_str
        self.has_thumbnail = post_info.has_thumbnail

    def priority(self):
        if self.has_thumbnail:
            return 1
        else:
            return 0

    def __repr__(self):
        return f"FetchPostQueueItem({self.actor_info.actor_name}, {self.post_id})"
