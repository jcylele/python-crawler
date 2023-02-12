DefaultRetryTimes = 5


class BaseQueueItem(object):
    def __init__(self):
        self.retry_times = DefaultRetryTimes

    def priority(self):
        return 0

    def onFailed(self):
        self.retry_times -= 1

    def canTry(self):
        return self.retry_times >= 0

    def __gt__(self, other):
        return self.priority() > other.priority()

    def __lt__(self, other):
        return self.priority() < other.priority()

