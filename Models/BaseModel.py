# Data Models consistent with table structs in database
import base64
import json
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

import Configs
from Consts import ResState, ResType
from Ctrls import FileInfoCacheCtrl, RequestCtrl
from Ctrls.FileInfoCacheCtrl import ActorFileInfo
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
        method = getattr(obj, 'toJson', None)
        if callable(method):
            return method()
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

    actor_name: Mapped[str] = mapped_column(
        ForeignKey("tab_actor.actor_name"),
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

    actor_name: Mapped[str] = mapped_column(String(30), primary_key=True)
    actor_category: Mapped[int] = mapped_column(ForeignKey("tab_actor_group.group_id"))
    actor_platform: Mapped[str] = mapped_column(String(30))
    actor_link: Mapped[str] = mapped_column(String(30))
    total_post_count: Mapped[int] = mapped_column(default=0)
    remark: Mapped[str] = mapped_column(String(100))
    main_actor: Mapped[str] = mapped_column(String(30))
    score: Mapped[int] = mapped_column(default=0)
    last_post_id: Mapped[int] = mapped_column(BigInteger, default=0)
    category_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    actor_group: Mapped["ActorGroupModel"] = relationship()
    post_list: Mapped[list["PostModel"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan"
    )
    rel_tags: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="actor",
        # order_by="ActorTagRelationship.tag.tag_priority"
    )

    def setCategory(self, new_category):
        if self.actor_category == new_category:
            return
        self.actor_category = new_category
        self.category_time = func.now()

    def toJson(self):
        json_data = {
            'actor_name': self.actor_name,
            'actor_category': self.actor_category,
            'score': self.score,
            'href': RequestCtrl.formatActorHref(self.actor_platform, self.actor_link),
            'has_main_actor': not IsStringEmpty(self.main_actor)
        }
        # remark encode for url
        remark = self.remark
        if IsStringEmpty(remark):
            json_data['remark'] = ""
        else:
            json_data['remark'] = base64.b64encode(remark.encode('utf-8')).decode('utf-8')
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
        return f"Actor(name={self.actor_name!r}, category={self.actor_category!r})"


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
    actor_name: Mapped[str] = mapped_column(ForeignKey("tab_actor.actor_name"))
    actor: Mapped["ActorModel"] = relationship(back_populates="post_list")
    completed: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(String(100))
    res_list: Mapped[list["ResModel"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="ResModel.res_index"
    )

    def __repr__(self) -> str:
        return f"Post(post_id={self.post_id!r}, actor_name={self.actor_name})"


class ResModel(BaseModel):
    __tablename__ = "tab_res"

    res_id: Mapped[int] = mapped_column(primary_key=True)
    res_url: Mapped[str] = mapped_column(String)
    res_index: Mapped[int] = mapped_column()
    res_state: Mapped[ResState] = mapped_column(IntEnum(ResState), default=ResState.Init)
    res_type: Mapped[ResType] = mapped_column(IntEnum(ResType))
    res_size: Mapped[int] = mapped_column(default=0)

    post_id: Mapped[int] = mapped_column(ForeignKey("tab_post.post_id", ondelete="CASCADE"))
    post: Mapped["PostModel"] = relationship(back_populates="res_list")

    def fileName(self) -> str:
        ext = self.res_url.split('.')[-1]
        return f"{self.post_id}_{self.res_index}.{ext}"

    def filePath(self) -> str:
        """
        real location for valid resources
        :return:
        """
        return f"{Configs.RootFolder}\\{self.post.actor_name}\\{self.fileName()}"

    def tmpFileName(self) -> str:
        return f"{self.post.actor_name}_{self.fileName()}"

    def tmpFilePath(self) -> str:
        """
        temporary location for resources before validation
        :return:
        """
        return f"{Configs.formatTmpFolderPath()}/{self.tmpFileName()}"

    def shouldDownload(self, max_file_size: int) -> bool:
        """
        check whether resources should be downloaded
        :return:
        """
        if self.res_state == ResState.Init:
            return True
        if self.res_state != ResState.Skip:
            return False
        if self.res_size > max_file_size > 0:
            # LogUtil.info(f"({self.res_id} of {self.post_id} of {self.post.actor_name}) too big: {self.res_size}")
            return False
        return True

    def setSize(self, size: int):
        if self.res_size > 0:
            if self.res_size == size:
                LogUtil.warn(
                    f"({self.res_id} of {self.post_id} of {self.post.actor_name}) size already set: {self.res_size}")
            else:
                LogUtil.error(
                    f"({self.res_id} of {self.post_id} of {self.post.actor_name}) size error, old {self.res_size}, new {size}")
            return
        self.res_size = size
        # update actor file info
        actor_name = self.post.actor_name
        actor_file_info = FileInfoCacheCtrl.GetCachedFileSizes(actor_name)
        if actor_file_info is not None:
            actor_file_info.onResSizeChanged(self)

    def setState(self, state: ResState):
        if self.res_state == state:
            return
        FileInfoCacheCtrl.OnFileStateChanged(self.post.actor_name, self, state)
        self.res_state = state

    def __repr__(self) -> str:
        return f"Res(id={self.res_id!r}, " \
               f"post_id={self.post_id}, " \
               f"index={self.res_index}, " \
               f"type={self.res_type}, " \
               f"size={self.res_size}, " \
               f"status={self.res_state}, " \
               f"url={self.res_url}) "
