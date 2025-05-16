from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import mapped_column, Mapped

from Configs import DB_STR_LEN_DOMAIN
from Models.BaseModel import BaseModel


class ResDomainModel(BaseModel):
    __tablename__ = "tab_res_domains"

    domain_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    domain_name: Mapped[str] = mapped_column(
        String(DB_STR_LEN_DOMAIN), unique=True)  # domain name
