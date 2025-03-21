from sqlalchemy.orm import Session
from sqlalchemy import update, func, select
from Consts import NoticeType
from Models.NoticeModel import NoticeModel
from Utils import LogUtil


def getNoticeCountMap(session: Session):
    _query = select(NoticeModel.notice_type, func.count(NoticeModel.notice_id)) \
        .where(NoticeModel.deleted == False) \
        .group_by(NoticeModel.notice_type)
    ret = session.execute(_query).fetchall()
    return [{'notice_type': notice_type, 'count': count} for notice_type, count in ret]


def getNoticesOfType(session: Session, notice_type: NoticeType, limit: int = 0, offset: int = 0) -> list[NoticeModel]:
    """
    get all notice of a certain type
    """
    stmt = (select(NoticeModel)
            .filter(NoticeModel.notice_type == notice_type)
            .filter(NoticeModel.deleted == False)
            .order_by(NoticeModel.notice_param0))
    if limit != 0:
        stmt = stmt.limit(limit)
    if offset != 0:
        stmt = stmt.offset(offset)
    notices = session.scalars(stmt)
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


def addNoticeStrict(session: Session, notice_type: NoticeType, params: list[str]):
    """
    add a notice, but params should be strictly sorted and distinct
    """
    strict_params = sortedDistinctNames(params)
    addNotice(session, notice_type, *strict_params)


def addNotice(session: Session, notice_type: NoticeType, *params):
    """
    add a notice
    """

    # length of params should <= 4, otherwise truncate it
    if len(params) > 4:
        LogUtil.warn(f"too many params {params} for notice type {notice_type}")
        params = params[:4]

    notice = NoticeModel()
    notice.notice_type = notice_type
    notice.setParams(*params)
    notices = (session.query(NoticeModel)
               .filter(NoticeModel.notice_checksum == notice.notice_checksum)
               .filter(NoticeModel.notice_type == notice_type)
               .all())
    if len(notices) > 0:
        for n in notices:
            # check if the notice already exists
            if notice.isSameParams(n):
                return
        # different params, same checksum
        LogUtil.warn(f"notice checksum conflict {notice.notice_checksum}")
    session.add(notice)
    session.flush()


def sortedDistinctNames(names: list[str]):
    names.sort()
    distinct_names = []
    for name in names:
        if name != "" and (len(distinct_names) == 0 or name != distinct_names[-1]):
            distinct_names.append(name)
    return distinct_names
