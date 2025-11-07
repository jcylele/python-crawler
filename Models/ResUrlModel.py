from sqlalchemy import String, ForeignKey, VARBINARY
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Configs import DB_BYTES_LEN_SHA256, DB_STR_LEN_EXTENSION
from Models.BaseModel import BaseModel
from Utils import PyUtil


class ResUrlModel(BaseModel):
    __tablename__ = "tab_res_url"

    url_id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(
        ForeignKey("tab_res_domains.domain_id"))
    hash_binary: Mapped[bytes] = mapped_column(
        VARBINARY(DB_BYTES_LEN_SHA256))  # 二进制存储哈希
    extension: Mapped[str] = mapped_column(String(DB_STR_LEN_EXTENSION))

    domain: Mapped["ResDomainModel"] = relationship()

    res: Mapped["ResModel"] = relationship(
        back_populates="res_url_info",
        uselist=False
    )

    @property
    def hash_hex(self) -> str:
        return PyUtil.bytes2hex(self.hash_binary)

    @property
    def full_url(self) -> str:
        """重构完整URL"""
        hex_sha256 = PyUtil.bytes2hex(self.hash_binary)
        hash_part = f"{hex_sha256[:2]}/{hex_sha256[2:4]}/{hex_sha256}"
        return f"https://{self.domain_name}/data/{hash_part}.{self.extension}"

    @property
    def file_name(self) -> str:
        hex_sha256 = PyUtil.bytes2hex(self.hash_binary)
        return f"{hex_sha256}.{self.extension}"

    @property
    def domain_name(self) -> str:
        return self.domain.domain_name
