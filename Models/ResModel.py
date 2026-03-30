from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

import Configs
from Consts import ResState, ResType
from Download.DownloadLimit import DownloadLimit
from Models.BaseModel import BaseModel, IntEnum
from Utils import LogUtil


class ResModel(BaseModel):
    __tablename__ = "tab_res"

    res_id: Mapped[int] = mapped_column(primary_key=True)
    res_url_id: Mapped[int] = mapped_column(
        ForeignKey("tab_res_url.url_id", ondelete="CASCADE"),
        index=True
    )
    res_index: Mapped[int] = mapped_column()
    res_state: Mapped[ResState] = mapped_column(
        IntEnum(ResState), default=ResState.Init)
    res_type: Mapped[ResType] = mapped_column(IntEnum(ResType))
    res_size: Mapped[int] = mapped_column(BigInteger, default=0)
    res_duration: Mapped[int] = mapped_column(default=0)
    res_width: Mapped[int] = mapped_column(default=0)
    res_height: Mapped[int] = mapped_column(default=0)

    post_id: Mapped[int] = mapped_column(
        ForeignKey("tab_post.post_id", ondelete="CASCADE"),
        index=True
    )

    __table_args__ = (
        Index('idx_post_id_res_index', 'post_id', 'res_index', unique=True),
    )

    res_url_info: Mapped["ResUrlModel"] = relationship(
        back_populates="res",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    post: Mapped["PostModel"] = relationship(
        back_populates="res_list",
        cascade="all",
        passive_deletes=True
    )

    def full_url(self) -> str:
        return self.res_url_info.full_url

    def actor(self):
        return self.post.actor

    def actor_id(self):
        return self.post.actor_id

    def filePath(self) -> str:
        """
        real location for valid resources
        :return:
        """
        actor = self.actor()
        actor_folder = Configs.formatActorFolderPath(
            actor.actor_id, actor.actor_name)
        ext = self.res_url_info.extension
        return f"{actor_folder}\\{self.post_id}_{self.res_index}.{ext}"

    def tmpFilePath(self) -> str:
        """
        temporary location for resources before validation
        :return:
        """
        ext = self.res_url_info.extension
        return f"{Configs.formatDownloadingFolderPath()}/{self.actor().actor_id}_{self.post_id}_{self.res_id}.{ext}"

    def isCompleted(self) -> bool:
        return self.res_state != ResState.Init

    def shouldDownload(self, download_limit: DownloadLimit) -> bool:
        if self.isCompleted():
            return False

        # 类型
        if not download_limit.allowResDownload(self.res_type):
            return False
        # 超过大小
        if not download_limit.checkResSize(self.res_size):
            return False

        return True

    def setSize(self, size: int) -> bool:
        actor_name = self.actor().actor_name
        if self.res_size > 0:
            if self.res_size == size:
                LogUtil.warning(
                    f"({self.res_id} of {self.post_id} of {actor_name}) size already set: {self.res_size}")
            else:
                LogUtil.error(
                    f"({self.res_id} of {self.post_id} of {actor_name}) size error, old {self.res_size}, new {size}")
            return False
        self.res_size = size

        return True

    def setState(self, state: ResState) -> bool:
        if self.res_state == state:
            return False
        self.res_state = state
        if state == ResState.Down:
            self.was_downloaded = True
        return True

    def setMediaInfo(self, info: tuple[int, int, int]) -> bool:
        if info[0] > 0 and info[1] > 0:
            self.res_width = info[0]
            self.res_height = info[1]
            self.res_duration = info[2]
            return True
        self.res_width = -1
        self.res_height = -1
        self.res_duration = 0
        return False

    def __repr__(self) -> str:
        return f"Res(id={self.res_id!r}, " \
               f"post_id={self.post_id}, " \
               f"index={self.res_index}, " \
               f"type={self.res_type}, " \
               f"size={self.res_size}, " \
               f"status={self.res_state}) "
