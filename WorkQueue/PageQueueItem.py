from WorkQueue.BaseQueueItem import BaseQueueItem
from WorkQueue.ExtraInfo import BaseExtraInfo


class PageQueueItem(BaseQueueItem):
    def __init__(self, url: str, content: str, extra_info: BaseExtraInfo):
        super().__init__()
        self.url = url
        self.content = content
        self.extra_info = extra_info

    def __repr__(self):
        return f"PageQueueItem(extra_info={self.extra_info})"


