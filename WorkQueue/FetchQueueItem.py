from WorkQueue.BaseQueueItem import BaseQueueItem


class FetchActorsQueueItem(BaseQueueItem):
    """
    fetch actor list
    """

    def __repr__(self):
        return f"FetchActorsQueueItem"


class FetchActorQueueItem(BaseQueueItem):
    """
    fetch a single actor
    """

    def __init__(self, actor_name: str):
        super().__init__()
        self.actor_name = actor_name

    def __repr__(self):
        return f"FetchActorQueueItem({self.actor_name})"
