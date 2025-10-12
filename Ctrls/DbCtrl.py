# database connection related operations
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.responses import Response

import Configs
from Consts import CacheKey
from Models.BaseModel import BaseModel

__Session = None


def init():
    global __Session
    if __Session is not None:
        return
    """
    init database
    """
    engine = create_engine(Configs.getSetting(CacheKey.DbConnectString), echo=False)

    # create all table if not exist
    BaseModel.metadata.create_all(engine)

    __Session = sessionmaker(engine)


def get_db_session():
    """FastAPI Dependency to get a DB session."""
    session = getSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def getSession() -> Session:
    """new a reusable session, caller manage the session"""
    return __Session()


def innerSession(connection) -> Session:
    return sessionmaker(bind=connection)()


def CustomJsonResponse(json_data) -> Response:
    str_data = json.dumps(json_data)
    return Response(content=str_data, media_type="application/text")
