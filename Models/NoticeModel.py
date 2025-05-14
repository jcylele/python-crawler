import hashlib

from sqlalchemy import Index, String, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from Consts import NoticeType
from Models.BaseModel import BaseModel, IntEnum


class NoticeModel(BaseModel):
    __tablename__ = "tab_notice"

    notice_id: Mapped[int] = mapped_column(primary_key=True)
    notice_type: Mapped[NoticeType] = mapped_column(IntEnum(NoticeType))
    notice_checksum: Mapped[str] = mapped_column(String(32))
    notice_param0: Mapped[str] = mapped_column(String(100), default="")
    notice_param1: Mapped[str] = mapped_column(String(100), default="")
    notice_param2: Mapped[str] = mapped_column(String(100), default="")
    notice_param3: Mapped[str] = mapped_column(String(100), default="")
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
        hasher.update(str(self.notice_type).encode('utf-8'))
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
        self.notice_param0 = param0
        self.notice_param1 = param1
        self.notice_param2 = param2
        self.notice_param3 = param3
        self.refreshChecksum()

    def refreshChecksum(self):
        self.notice_checksum = self.__checksum()

    def check(self):
        true_checksum = self.__checksum()
        if true_checksum != self.notice_checksum:
            print(f"NoticeModel check failed! {self.notice_id} {self.notice_type} {self.notice_param0} {self.notice_param1} {self.notice_param2} {self.notice_param3} {self.notice_checksum} {true_checksum}")
            return False

        return True

    def toJson(self):
        json_data = {
            'notice_id': self.notice_id,
            'notice_param0': self.notice_param0,
            'notice_param1': self.notice_param1,
            'notice_param2': self.notice_param2,
            'notice_param3': self.notice_param3
        }

        return json_data
