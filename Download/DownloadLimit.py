from sqlalchemy import Select

from Consts import ResType, PostFilter
from routers.web_data import DownloadLimitForm
from routers.schemas_others import DownloadLimitResponse, DownloadProgress


class DownloadLimit(object):

    def __init__(self, form: DownloadLimitForm):
        self.limit = form
        self.progress = DownloadProgress()

    def onActor(self):
        self.progress.actor_count += 1

    def moreActor(self) -> bool:
        return self.limit.actor_count == 0 or self.progress.actor_count < self.limit.actor_count

    def getPostFilter(self) -> PostFilter:
        return PostFilter(self.limit.post_filter)

    def morePost(self, post_count: int) -> bool:
        return self.limit.post_count == 0 or post_count < self.limit.post_count

    def onPost(self):
        self.progress.post_count += 1

    def allowResDownload(self, res_type: ResType) -> bool:
        return self.limit.res_type == res_type.value

    def allowResInfo(self, res_type: ResType) -> bool:
        return self.limit.res_type <= res_type.value

    def canResInfo(self, res_type: ResType) -> bool:
        """
        skip unneeded res info
        """
        if res_type == ResType.Video:
            return True
        if self.progress.file_count >= self.limit.file_count > 0:
            return False
        return True

    def checkResSize(self, res_size: int) -> bool:
        return not (res_size > self.limit.single_file_size > 0)

    def canDownload(self, file_size: int) -> bool:
        if self.progress.file_count >= self.limit.file_count > 0:
            return False
        if self.progress.total_file_size + file_size > self.limit.total_file_size > 0:
            return False
        return True

    def onDownloaded(self, file_size: int):
        self.progress.total_file_size += file_size
        self.progress.file_count += 1

    def toResponse(self) -> DownloadLimitResponse:
        return DownloadLimitResponse(limit=self.limit, progress=self.progress)
