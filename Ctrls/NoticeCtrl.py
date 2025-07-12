from sqlalchemy.orm import Session
from sqlalchemy import update, func, select, or_
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
    do nothing if there is actually only one distinct param
    """
    strict_params = sortedDistinctNames(params)
    # if there is only one param, SameActorName notice is already handled
    if len(strict_params) <= 1:
        return
    addNotice(session, notice_type, *strict_params)


_LESS_IMPORTANT_NOTICE_TYPES = [
    NoticeType.SimilarActorName
]


def addNotice(session: Session, notice_type: NoticeType, *params):
    """
    add a notice
    """

    # length of params should <= 4, otherwise truncate it
    if len(params) > 4:
        LogUtil.warn(f"too many params {params} for notice type {notice_type}")
        params = params[:4]

    notice = NoticeModel(
        notice_type=notice_type,
    )
    notice.setParams(*params)
    stmt = (select(NoticeModel)
            .where(NoticeModel.notice_checksum == notice.notice_checksum))
    notices = session.scalars(stmt)
    for n in notices:
        # check if the notice already exists, skip if it is a less important notice
        if notice.notice_type in _LESS_IMPORTANT_NOTICE_TYPES and notice.isSameParams(n):
            return
        # different params, same checksum
        LogUtil.warn(f"notice checksum conflict {notice.notice_checksum}")

    session.add(notice)
    session.flush()


def searchNotice(session: Session, actor_name: str):
    """
    search a notice
    """
    stmt = (select(NoticeModel)
            .where(or_(
                NoticeModel.notice_param0 == actor_name,
                NoticeModel.notice_param1 == actor_name,
                NoticeModel.notice_param2 == actor_name,
                NoticeModel.notice_param3 == actor_name
            ))
            .order_by(NoticeModel.notice_id))
    notices = session.scalars(stmt)
    return [notice for notice in notices]


def sortedDistinctNames(names: list[str]):
    return sorted(set(filter(lambda x: x != "", map(str.lower, names))))


def regenerateCheckSums(session: Session):
    stmt = (select(NoticeModel))
    notices = session.scalars(stmt)
    for notice in notices:
        notice.refreshChecksum()
