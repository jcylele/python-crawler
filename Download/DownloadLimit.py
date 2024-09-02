from enum import IntEnum

from routers.web_data import DownloadLimitForm


class PostFilter(IntEnum):
    Normal = 0
    Current = 1


class DownloadLimit(object):

    def __init__(self, form: DownloadLimitForm):
        self.actor_count = form.actor_count
        self.__left_actor_count = form.actor_count
        self.post_count = form.post_count
        self.file_size = form.file_size
        self.total_file_size = form.total_file_size
        self.downloaded_file_size = 0
        self.post_filter = PostFilter(form.post_filter)
        self.allow_video = form.allow_video
        self.allow_img = form.allow_img

    def canDownload(self, file_size: int) -> bool:
        if self.total_file_size == 0:
            return True
        return file_size <= self.total_file_size - self.downloaded_file_size

    def onDownloaded(self, file_size: int):
        self.downloaded_file_size += file_size

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

    def toJson(self):
        return {
            "actor_count": self.actor_count,
            "post_count": self.post_count,
            "file_size": self.file_size,
            "total_file_size": self.total_file_size,
            "post_filter": self.post_filter.value,
            "allow_video": self.allow_video,
            "allow_img": self.allow_img,
        }
