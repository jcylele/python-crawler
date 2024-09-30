from sqlalchemy.orm import Session

from Consts import NoticeType
from Models.BaseModel import NoticeModel


def getNoticesOfType(session: Session, notice_type: NoticeType) -> list[NoticeModel]:
    """
    get all notice of a certain type
    """
    notices = session.query(NoticeModel).filter(NoticeModel.notice_type == notice_type).all()
    return [notice for notice in notices]


def deleteNotice(session: Session, notice_id: int):
    """
    delete a notice by its id
    """
    notice = session.get(NoticeModel, notice_id)
    if notice is None:
        return
    session.delete(notice)


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
