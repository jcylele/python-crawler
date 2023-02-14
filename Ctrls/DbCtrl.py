# database connection related operations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import Configs
from Models.BaseModel import BaseModel

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
