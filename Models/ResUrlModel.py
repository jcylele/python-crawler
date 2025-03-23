from sqlalchemy import String, ForeignKey, LargeBinary
from sqlalchemy.orm import mapped_column, Mapped, relationship

from Models.BaseModel import BaseModel
from Utils import PyUtil


class ResUrlModel(BaseModel):
    __tablename__ = "tab_res_url"

    url_id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("tab_res_domains.domain_id"))
    hash_binary: Mapped[bytes] = mapped_column(LargeBinary(32))  # 二进制存储哈希
    extension: Mapped[str] = mapped_column(String(10))

    domain: Mapped["ResDomainModel"] = relationship()

    res: Mapped["ResModel"] = relationship(
        back_populates="res_url_info",
        uselist=False
    )

    @property
    def full_url(self) -> str:
        """重构完整URL"""
        hex_sha256 = PyUtil.bytes2hex(self.hash_binary)
        hash_part = f"{hex_sha256[:2]}/{hex_sha256[2:4]}/{hex_sha256}"
        return f"https://{self.domain.domain_name}/data/{hash_part}.{self.extension}"
