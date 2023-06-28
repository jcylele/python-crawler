class DownloadLimit(object):
    def __init__(self, actor_count: int, post_count: int, file_size: int):
        self.actor_count = actor_count
        self.__left_actor_count = actor_count
        self.post_count = post_count
        self.file_size = file_size

    def moreActor(self, use: bool) -> bool:
        """
        continue to enqueue new actors or not
        :param use decrease the number
        """
        if self.__left_actor_count > 0:
            if use:
                self.__left_actor_count -= 1
            return True
        return False

    def __repr__(self) -> str:
        return f"({self.actor_count}/{self.post_count}/{self.file_size})"

