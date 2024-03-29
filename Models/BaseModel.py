# Data Models consistent with table structs in database
import json
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

import Configs
from Ctrls import FileInfoCacheCtrl, RequestCtrl


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
        if isinstance(obj, BaseModel):
            return obj.toJson()
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


class ActorCategory(Enum):
    Init = 1  # initial state of an actor
    Liked = 2  # mark as liked
    Dislike = 3  # dislike and remove the folder
    Enough = 4  # once liked, then remove the folder


class ActorModel(BaseModel):
    __tablename__ = "tab_actor"

    actor_name: Mapped[str] = mapped_column(String(30), primary_key=True)
    actor_category: Mapped[ActorCategory] = mapped_column(IntEnum(ActorCategory), default=ActorCategory.Init)
    actor_platform: Mapped[str] = mapped_column(String(30))
    actor_link: Mapped[str] = mapped_column(String(30))
    completed: Mapped[bool] = mapped_column(default=False)
    star: Mapped[bool] = mapped_column(default=False)

    post_list: Mapped[list["PostModel"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan"
    )
    rel_tags: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="actor",
        # order_by="ActorTagRelationship.tag.tag_priority"
    )

    def toJson(self):
        json_data = super().toJson()
        tag_list = []

        for tag in self.rel_tags:
            tag_list.append(tag.tag_id)
        json_data['rel_tags'] = tag_list

        info = FileInfoCacheCtrl.GetFileInfo(self.actor_name)
        json_data['file_info'] = info

        json_data['href'] = RequestCtrl.formatActorHref(self.actor_platform, self.actor_link)

        return json_data

    def __repr__(self) -> str:
        return f"Actor(name={self.actor_name!r}, category={self.actor_category!r})"


class ActorTagModel(BaseModel):
    __tablename__ = "tab_actor_tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(30))
    tag_priority: Mapped[int] = mapped_column(default=0)
    tag_color: Mapped[str] = mapped_column(String(30), default="#FFFFFF")

    rel_actors: Mapped[list["ActorTagRelationship"]] = relationship(
        back_populates="tag"
    )


class PostModel(BaseModel):
    __tablename__ = "tab_post"

    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_name: Mapped[str] = mapped_column(ForeignKey("tab_actor.actor_name"))
    actor: Mapped["ActorModel"] = relationship(back_populates="post_list")
    completed: Mapped[bool] = mapped_column(default=False)
    res_list: Mapped[list["ResModel"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="ResModel.res_index"
    )

    def __repr__(self) -> str:
        return f"Post(post_id={self.post_id!r}, actor_name={self.actor_name})"


class ResType(Enum):
    Image = 1
    Video = 2


class ResState(Enum):
    Init = 1
    Down = 2
    Skip = 3
    Del = 4


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
        if self.res_size > max_file_size:
            # LogUtil.info(f"({self.res_id} of {self.post_id} of {self.post.actor_name}) too big: {self.res_size}")
            return False
        return True

    def __repr__(self) -> str:
        return f"Res(id={self.res_id!r}, " \
               f"post_id={self.post_id}, " \
               f"index={self.res_index}, " \
               f"type={self.res_type}, " \
               f"size={self.res_size}, " \
               f"status={self.res_state}, " \
               f"url={self.res_url}) "
