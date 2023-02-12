from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

__Session = None


def init():
    """
    初始化数据库相关
    """
    # db_path = Consts.formatRecordPath()
    engine = create_engine("mysql+pymysql://jcylele:2613561@localhost:3306/onlyfans", echo=False, future=True)
    # BaseModel.metadata.create_all(engine)

    global __Session
    __Session = sessionmaker(engine)


def getSession() -> Session:
    """
    新建一个session
    :return: Session
    """
    return __Session()







