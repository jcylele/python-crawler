import hashlib

from sqlalchemy import Index, String
from sqlalchemy.orm import mapped_column, Mapped

from Configs import DB_STR_LEN_MD5, DB_STR_LEN_LONG
from Consts import NoticeType
from Models.BaseModel import BaseModel, IntEnum


class NoticeModel(BaseModel):
    __tablename__ = "tab_notice"

    notice_id: Mapped[int] = mapped_column(primary_key=True)
    notice_type: Mapped[NoticeType] = mapped_column(IntEnum(NoticeType))
    notice_checksum: Mapped[str] = mapped_column(String(DB_STR_LEN_MD5))
    notice_param0: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), default="")
    notice_param1: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), default="")
    notice_param2: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), default="")
    notice_param3: Mapped[str] = mapped_column(
        String(DB_STR_LEN_LONG), default="")
    deleted: Mapped[bool] = mapped_column(default=False)

    # 添加复合索引
    __table_args__ = (
        Index('idx_notice_type_checksum', notice_type, notice_checksum),
    )

    def __checksum(self) -> str:
        hasher = hashlib.md5()

        for param in [self.notice_param0, self.notice_param1,
                      self.notice_param2, self.notice_param3]:
            hasher.update(str(param).encode('utf-8'))
        return hasher.hexdigest()

    def isSameParams(self, other: "NoticeModel"):
        return (self.notice_param0 == other.notice_param0
                and self.notice_param1 == other.notice_param1
                and self.notice_param2 == other.notice_param2
                and self.notice_param3 == other.notice_param3)

    def setParams(self, param0: str, param1: str = "", param2: str = "", param3: str = ""):
        """
        set parameters and calculate checksum
        """
        self.notice_param0 = str.lower(param0)
        self.notice_param1 = str.lower(param1)
        self.notice_param2 = str.lower(param2)
        self.notice_param3 = str.lower(param3)
        self.refreshChecksum()

    def refreshChecksum(self):
        self.notice_checksum = self.__checksum()

    def check(self):
        true_checksum = self.__checksum()
        if true_checksum != self.notice_checksum:
            print(
                f"NoticeModel check failed! {self.notice_id} {self.notice_type} {self.notice_param0} {self.notice_param1} {self.notice_param2} {self.notice_param3} {self.notice_checksum} {true_checksum}")
            return False

        return True
