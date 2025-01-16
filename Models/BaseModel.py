# Data Models consistent with table structs in database
import base64
import json
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

import Configs
from Consts import ResState, ResType, NoticeType, ActorLogType
from Ctrls import FileInfoCacheCtrl, RequestCtrl
from Ctrls.FileInfoCacheCtrl import ActorFileInfo
from Download.DownloadLimit import DownloadLimit
from Utils import LogUtil


def IsStringEmpty(s: str):
    return s is None or len(s) == 0


class IntEnum(sa.types.TypeDecorator):
    """
    convert between enum in python and integer in database
    """

    impl = sa.Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        """
        from python to database
        """
        return value.value

    def process_result_value(self, value, dialect):
        """
        from database to python
        """
        return self._enumtype(value)


class BaseModelEncoder(json.JSONEncoder):
    """
    json encoder for BaseModel
    """

    def default(self, obj):
        # custom toJson
        method = getattr(obj, 'toJson', None)
        if callable(method):
            return method()
        # enum value
        if isinstance(obj, Enum):
            return obj.value
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class BaseModel(DeclarativeBase):
    def toJson(self):
        json_data = {}
        for c in self.__table__.columns:
            attr = getattr(self, c.name)
            if isinstance(attr, Enum):
                attr = attr.value

            if attr is not None:
                json_data[c.name] = attr

        return json_data


class ActorTagRelationship(BaseModel):
    __tablename__ = "rel_actor_tag"

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id"),
        primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor_tag.tag_id"),
        primary_key=True
    )

    tag: Mapped["ActorTagModel"] = relationship(back_populates="rel_actors")
    actor: Mapped["ActorModel"] = relationship(back_populates="rel_tags")


class ActorModel(BaseModel):
    __tablename__ = "tab_actor"

    actor_id: Mapped[int] = mapped_column(primary_key=True)
    actor_name: Mapped[str] = mapped_column(String(30))
    actor_group_id: Mapped[int] = mapped_column(ForeignKey("tab_actor_group.group_id"))
    actor_platform: Mapped[str] = mapped_column(String(30))
    actor_link: Mapped[str] = mapped_column(String(30))
    total_post_count: Mapped[int] = mapped_column(default=0)
    remark: Mapped[str] = mapped_column(String(100))
    main_actor_id: Mapped[int] = mapped_column(default=0)
    score: Mapped[int] = mapped_column(default=0)
    group_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())
    last_post_id: Mapped[int] = mapped_column(BigInteger, default=0)

    actor_group: Mapped["ActorGroupModel"] = relationship()
    post_list: Mapped[list["PostModel"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan"
    )
    rel_tags: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="actor",
        # order_by="ActorTagRelationship.tag.tag_priority"
    )

    def setGroup(self, group_id):
        if self.actor_group_id == group_id:
            return
        self.actor_group_id = group_id
        self.group_time = func.now()

    def toJson(self):
        json_data = {
            'actor_id': self.actor_id,
            'actor_name': self.actor_name,
            'actor_group_id': self.actor_group_id,
            'score': self.score,
            'href': RequestCtrl.formatActorHref(self.actor_platform, self.actor_link),
            'has_main_actor': self.main_actor_id != 0
        }
        # remark encode for url
        remark = self.remark
        if not remark:
            json_data['remark'] = ""
        else:
            json_data['remark'] = base64.b64encode(remark.encode('utf-8')).decode('utf-8')
        # posts with comment
        post_list = []
        for post in self.post_list:
            if post.comment:
                post_list.append(post.toJson())
        json_data['commented_posts'] = post_list
        # tag ids
        tag_list = []
        for tag in self.rel_tags:
            tag_list.append(tag.tag_id)
        json_data['tag_ids'] = tag_list

        return json_data

    def calc_res_file_info(self) -> ActorFileInfo:
        actor_file_info = ActorFileInfo()
        for post in self.post_list:
            for res in post.res_list:
                actor_file_info.addRes(res)
        return actor_file_info

    def __repr__(self) -> str:
        return f"Actor(name={self.actor_name!r}, group={self.actor_group.group_name!r})"


class ActorTagModel(BaseModel):
    __tablename__ = "tab_actor_tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(30))
    tag_priority: Mapped[int] = mapped_column(default=0)

    rel_actors: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="tag"
    )


class ActorGroupModel(BaseModel):
    __tablename__ = "tab_actor_group"

    group_id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str] = mapped_column(String(30))
    group_desc: Mapped[str] = mapped_column(String(100))
    group_color: Mapped[str] = mapped_column(String(20))
    has_folder: Mapped[bool] = mapped_column(default=False)
    group_priority: Mapped[int] = mapped_column(default=0)


class PostModel(BaseModel):
    __tablename__ = "tab_post"

    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("tab_actor.actor_id"))
    is_dm: Mapped[bool] = mapped_column(default=False)
    completed: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(String(100))

    actor: Mapped["ActorModel"] = relationship(back_populates="post_list")
    res_list: Mapped[list["ResModel"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="ResModel.res_index"
    )

    def toJson(self):
        return {
            # large number may be corrupted in js, so use string instead
            'post_id': str(self.post_id),
            'comment': self.comment
        }

    def __repr__(self) -> str:
        return f"Post(post_id={self.post_id!r}, actor_name={self.actor.actor_name})"


class ResModel(BaseModel):
    __tablename__ = "tab_res"

    res_id: Mapped[int] = mapped_column(primary_key=True)
    res_url: Mapped[str] = mapped_column(String(200))
    res_index: Mapped[int] = mapped_column()
    res_state: Mapped[ResState] = mapped_column(IntEnum(ResState), default=ResState.Init)
    res_type: Mapped[ResType] = mapped_column(IntEnum(ResType))
    res_size: Mapped[int] = mapped_column(default=0)

    post_id: Mapped[int] = mapped_column(ForeignKey("tab_post.post_id", ondelete="CASCADE"))
    post: Mapped["PostModel"] = relationship(back_populates="res_list")

    def actor_name(self):
        return self.post.actor.actor_name

    def actor_id(self):
        return self.post.actor_id

    def fileName(self) -> str:
        ext = self.res_url.split('.')[-1]
        return f"{self.post_id}_{self.res_index}.{ext}"

    def filePath(self) -> str:
        """
        real location for valid resources
        :return:
        """
        return f"{Configs.RootFolder}\\{self.actor_name()}\\{self.fileName()}"

    def tmpFileName(self) -> str:
        return f"{self.actor_name()}_{self.fileName()}"

    def tmpFilePath(self) -> str:
        """
        temporary location for resources before validation
        :return:
        """
        return f"{Configs.formatTmpFolderPath()}/{self.tmpFileName()}"

    def shouldDownload(self, downloadLimit: DownloadLimit) -> bool:
        # 已下载/删除
        if self.res_state == ResState.Down or self.res_state == ResState.Del:
            return False
        # 类型不对
        if self.res_type == ResType.Video:
            if not downloadLimit.allow_video:
                return False
        elif self.res_type == ResType.Image:
            if not downloadLimit.allow_img:
                return False
        # 超过大小
        if self.res_size > downloadLimit.file_size > 0:
            return False

        return True

    def setSize(self, size: int):
        actor_name = self.actor_name()
        if self.res_size > 0:
            if self.res_size == size:
                LogUtil.warn(
                    f"({self.res_id} of {self.post_id} of {actor_name}) size already set: {self.res_size}")
            else:
                LogUtil.error(
                    f"({self.res_id} of {self.post_id} of {actor_name}) size error, old {self.res_size}, new {size}")
            return
        self.res_size = size
        # update actor file info
        FileInfoCacheCtrl.OnFileSizeChanged(self.actor_id(), self)

    def setState(self, state: ResState):
        if self.res_state == state:
            return
        FileInfoCacheCtrl.OnFileStateChanged(self.actor_id(), self, state)
        self.res_state = state

    def __repr__(self) -> str:
        return f"Res(id={self.res_id!r}, " \
               f"post_id={self.post_id}, " \
               f"index={self.res_index}, " \
               f"type={self.res_type}, " \
               f"size={self.res_size}, " \
               f"status={self.res_state}) "


class NoticeModel(BaseModel):
    __tablename__ = "tab_notice"

    notice_id: Mapped[int] = mapped_column(primary_key=True)
    notice_type: Mapped[NoticeType] = mapped_column(IntEnum(NoticeType))
    notice_checksum: Mapped[str] = mapped_column(String(100))
    notice_param0: Mapped[str] = mapped_column(String(100), default="")
    notice_param1: Mapped[str] = mapped_column(String(100), default="")
    notice_param2: Mapped[str] = mapped_column(String(100), default="")
    deleted: Mapped[bool] = mapped_column(default=False)

    def __calcChecksum(self):
        bytes1 = self.notice_param0.encode('utf-8')
        bytes2 = self.notice_param1.encode('utf-8')
        bytes3 = self.notice_param2.encode('utf-8')
        xor_len = len(bytes1) ^ len(bytes2) ^ len(bytes3)
        max_len = max(len(bytes1), len(bytes2), len(bytes3))
        bytes1 = bytes1.ljust(max_len, b'\0')
        bytes2 = bytes2.ljust(max_len, b'\0')
        bytes3 = bytes3.ljust(max_len, b'\0')
        xor = bytearray(a ^ b ^ c for a, b, c in zip(bytes1, bytes2, bytes3))
        checksum = base64.encodebytes(xor).decode('utf-8').replace('\n', '')
        shift = xor_len % len(checksum)
        self.notice_checksum = checksum[shift:] + checksum[:shift]

    def sortedParams(self):
        """
        get sorted parameters
        """
        return sorted([self.notice_param0, self.notice_param1, self.notice_param2])

    def setParams(self, param0: str, param1: str = "", param2: str = ""):
        """
        set parameters and calculate checksum
        """
        self.notice_param0 = param0
        self.notice_param1 = param1
        self.notice_param2 = param2
        self.__calcChecksum()

    def toJson(self):
        json_data = {
            'notice_id': self.notice_id,
            'notice_param0': self.notice_param0,
            'notice_param1': self.notice_param1,
            'notice_param2': self.notice_param2
        }

        return json_data


class ActorLogModel(BaseModel):
    __tablename__ = "tab_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("tab_actor.actor_id"),
        index=True
    )
    log_type: Mapped[ActorLogType] = mapped_column(IntEnum(ActorLogType))
    log_param: Mapped[str] = mapped_column(String(100), default="")
    log_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    def toJson(self):
        json_data = {
            'log_type': self.log_type,
            'log_param': self.log_param,
        }

        return json_data
