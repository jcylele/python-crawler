# database connection related operations
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.responses import Response

import Configs
from Models.BaseModel import BaseModel, BaseModelEncoder

__Session = None


def init():
    global __Session
    if __Session is not None:
        return
    """
    init database
    """
    engine = create_engine(Configs.DbConnectString, echo=False)

    # create all table if not exist
    BaseModel.metadata.create_all(engine)

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



