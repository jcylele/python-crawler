from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from Consts import NoticeType
from Models.BaseModel import BaseModel, IntEnum


class NoticeModel(BaseModel):
    __tablename__ = "tab_notice"

    notice_id: Mapped[int] = mapped_column(primary_key=True)
    notice_type: Mapped[NoticeType] = mapped_column(IntEnum(NoticeType))
    notice_checksum: Mapped[str] = mapped_column(String(100))
    notice_param0: Mapped[str] = mapped_column(String(100), default="")
    notice_param1: Mapped[str] = mapped_column(String(100), default="")
    notice_param2: Mapped[str] = mapped_column(String(100), default="")
    notice_param3: Mapped[str] = mapped_column(String(100), default="")
    deleted: Mapped[bool] = mapped_column(default=False)

    def __checksum(self) -> str:
        """
        simple is the best
        """
        result = 17
        result = 37 * result + hash(self.notice_param0)
        result = 37 * result + hash(self.notice_param1)
        result = 37 * result + hash(self.notice_param2)
        result = 37 * result + hash(self.notice_param3)
        result = result << self.notice_type.value
        return str(result)

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

    def toJson(self):
        json_data = {
            'notice_id': self.notice_id,
            'notice_param0': self.notice_param0,
            'notice_param1': self.notice_param1,
            'notice_param2': self.notice_param2,
            'notice_param3': self.notice_param3
        }

        return json_data
