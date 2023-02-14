from WorkQueue.BaseQueueItem import BaseQueueItem
from WorkQueue.ExtraInfo import BaseExtraInfo


class UrlQueueItem(BaseQueueItem):
    """
    A queue item containing urls for getting or downloading and extra information
    """
    def __init__(self, url: str, from_url: str = None, extra_info: BaseExtraInfo = None):
        super().__init__()

        self.url = url
        self.from_url = from_url
        self.extra_info = extra_info

    def priority(self):
        return self.extra_info.priority()

    def __repr__(self):
        return f"UrlQueueItem(extra_info={self.extra_info})"


