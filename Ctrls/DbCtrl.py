# database connection related operations
import json

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker, Query
from starlette.responses import Response

import Configs
from Models.BaseModel import BaseModel, BaseModelEncoder

__Session = None


def init():
    """
    init database
    """
    engine = create_engine(Configs.DbConnectString, echo=False, future=True)

    # create all table if not exist
    BaseModel.metadata.create_all(engine)

    global __Session
    __Session = sessionmaker(engine)


def getSession() -> Session:
    """
    new a reusable session
    :return:
    """
    return __Session()


def CustomJsonResponse(json_data) -> Response:
    str_data = json.dumps(json_data, cls=BaseModelEncoder)
    return Response(content=str_data, media_type="application/text")


def queryCount(q: Query) -> int:
    count_q = q.statement.with_only_columns(func.count(), maintain_column_froms=True).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count
