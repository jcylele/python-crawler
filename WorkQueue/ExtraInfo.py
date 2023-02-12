from WorkQueue import QueueMgr


class BaseExtraInfo(object):
    def __init__(self):
        super().__init__()

    def queueType(self):
        raise NotImplementedError("")

    def priority(self):
        raise NotImplementedError("")


class ActorsExtraInfo(BaseExtraInfo):
    def __init__(self, start_order: int = 0):
        super().__init__()
        self.start_order = start_order

    def queueType(self):
        return QueueMgr.QueueType.AnalyseActors

    def priority(self):
        return 40000

    def __repr__(self) -> str:
        return f"(actors?o={self.start_order})"


class ActorExtraInfo(BaseExtraInfo):
    def __init__(self, actor_name: str, start_order: int = 0):
        super().__init__()
        self.actor_name = actor_name
        self.start_order = start_order

    def queueType(self):
        return QueueMgr.QueueType.AnalyseUser

    def priority(self):
        # 前排页面优先级较高
        return 30000 + self.start_order

    def __repr__(self) -> str:
        return f"({self.actor_name}?o={self.start_order})"


class PostExtraInfo(BaseExtraInfo):
    def __init__(self, actor_name: str, post_id: int):
        super().__init__()
        self.actor_name = actor_name
        self.post_id = post_id

    def queueType(self):
        return QueueMgr.QueueType.AnalysePost

    def priority(self):
        # 新的先下载
        return 20000 + 10000 - (self.post_id // 100000)

    def __repr__(self) -> str:
        return f"({self.post_id} of {self.actor_name})"


class ResExtraInfo(BaseExtraInfo):
    def __init__(self, actor_name: str, post_id: int, res_id: int):
        super().__init__()
        self.actor_name = actor_name
        self.post_id = post_id
        self.res_id = res_id

    def queueType(self):
        return QueueMgr.QueueType.ResInfo

    def priority(self):
        # 新的先下载
        return 10000 + 10000 - (self.post_id // 100000)

    def __repr__(self) -> str:
        return f"({self.res_id} of {self.post_id} of {self.actor_name})"


class ResFileExtraInfo(ResExtraInfo):
    def __init__(self, extra: ResExtraInfo, file_path: str, file_size: int):
        super().__init__(extra.actor_name, extra.post_id, extra.res_id)
        self.file_path = file_path
        self.file_size = file_size

    def queueType(self):
        return QueueMgr.QueueType.ResFile

    def priority(self):
        # 小文件优先下载
        return self.file_size

    def __repr__(self) -> str:
        return f"(file {self.res_id} of {self.post_id} of {self.actor_name})"