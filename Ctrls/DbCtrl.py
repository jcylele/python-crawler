# database connection related operations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

__Session = None
__db_url = "mysql+pymysql://jcylele:123456@localhost:3306/onlyfans"


def init():
    """
    init database
    """
    engine = create_engine(__db_url, echo=False, future=True)

    # create all table if not exist
    # BaseModel.metadata.create_all(engine)

    global __Session
    __Session = sessionmaker(engine)


def getSession() -> Session:
    """
    new a reusable session
    :return:
    """
    return __Session()
