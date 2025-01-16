from sqlalchemy.orm import Session
from sqlalchemy import update, func, select
from Consts import NoticeType
from Models.BaseModel import NoticeModel


def getNoticeCountMap(session: Session):
    _query = select(NoticeModel.notice_type, func.count(NoticeModel.notice_id)) \
        .where(NoticeModel.deleted == False) \
        .group_by(NoticeModel.notice_type)
    ret = session.execute(_query).fetchall()
    return [{'notice_type': notice_type, 'count': count} for notice_type, count in ret]


def getNoticesOfType(session: Session, notice_type: NoticeType) -> list[NoticeModel]:
    """
    get all notice of a certain type
    """
    notices = (session.query(NoticeModel)
               .filter(NoticeModel.notice_type == notice_type)
               .filter(NoticeModel.deleted == False)
               .all())
    return [notice for notice in notices]


def deleteNoticesOfType(session: Session, notice_type: NoticeType):
    _query = update(NoticeModel) \
        .where(NoticeModel.notice_type == notice_type) \
        .values(deleted=True)
    session.execute(_query)


def deleteNotice(session: Session, notice_id: int):
    _query = update(NoticeModel) \
        .where(NoticeModel.notice_id == notice_id) \
        .values(deleted=True)
    session.execute(_query)


def addNotice(session: Session, notice_type: NoticeType, param0: str, param1: str = "", param2: str = ""):
    """
    add a notice
    """
    notice = NoticeModel()
    notice.notice_type = notice_type
    notice.setParams(param0, param1, param2)
    notices = session.query(NoticeModel).filter(NoticeModel.notice_checksum == notice.notice_checksum).all()
    if len(notices) > 0:
        params = notice.sortedParams()
        for n in notices:
            # check if the notice already exists
            if n.sortedParams() == params:
                return n
    session.add(notice)
    session.flush()
    return notice
