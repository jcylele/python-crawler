
#
DefaultRetryTimes = 5


class BaseQueueItem(object):
    """
    base class for all queue items(tasks)
    """
    def __init__(self):
        self.left_retry_times = DefaultRetryTimes

    def priority(self):
        """
        for subclasses which are used in priorityqueue to override
        :return:
        """
        return 0

    def onFailed(self):
        self.left_retry_times -= 1

    def shouldRetry(self) -> bool:
        """
        should the item put back to the queue for another process
        :return:
        """
        return self.left_retry_times >= 0

    def __gt__(self, other: "BaseQueueItem"):
        if self.left_retry_times != other.left_retry_times:
            return self.left_retry_times > other.left_retry_times
        return self.priority() > other.priority()

    def __lt__(self, other):
        if self.left_retry_times != other.left_retry_times:
            return self.left_retry_times < other.left_retry_times
        return self.priority() < other.priority()

