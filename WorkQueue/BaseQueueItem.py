
#
DefaultRetryTimes = 5


class BaseQueueItem(object):
    """
    base class for all queue items(tasks)
    """
    def __init__(self):
        self.retry_times = DefaultRetryTimes

    def priority(self):
        """
        for subclasses which are used in priorityqueue to override
        :return:
        """
        return 0

    def onFailed(self):
        self.retry_times -= 1

    def shouldRetry(self) -> bool:
        """
        should the item put back to the queue for another process
        :return:
        """
        return self.retry_times >= 0

    def __gt__(self, other):
        return self.priority() > other.priority()

    def __lt__(self, other):
        return self.priority() < other.priority()

