from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import mapped_column, Mapped

from Models.BaseModel import BaseModel


class ResDomainModel(BaseModel):
    __tablename__ = "tab_res_domains"

    domain_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    domain_name: Mapped[str] = mapped_column(
        String(50), unique=True)  # domain name
