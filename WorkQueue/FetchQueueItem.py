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

    def __init__(self, actor_id: str):
        super().__init__()
        self.actor_id = actor_id

    def __repr__(self):
        return f"FetchActorQueueItem({self.actor_id})"
