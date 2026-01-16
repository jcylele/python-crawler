from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Consts import NoticeType
from Ctrls import DbCtrl, NoticeCtrl
from routers.schemas import NoticeResponse
from routers.schemas_others import CommonResponse, NoticeCount, UnifiedListResponse

router = APIRouter(
    prefix="/api/notice",
    tags=["notice"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/count_map", response_model=UnifiedListResponse[NoticeCount])
def get_notice_count(session: Session = Depends(DbCtrl.get_db_session)):
    return UnifiedListResponse[NoticeCount](data=NoticeCtrl.getNoticeCountMap(session))


@router.get("/list/{notice_type}", response_model=UnifiedListResponse[NoticeResponse])
def get_notices(notice_type: int, limit: int = 0, offset: int = 0, session: Session = Depends(DbCtrl.get_db_session)):
    notices = NoticeCtrl.getNoticesOfType(
        session, NoticeType(notice_type), limit, offset)
    return UnifiedListResponse[NoticeResponse](data=notices)


@router.delete("/list/{notice_type}", response_model=CommonResponse)
def delete_notices(notice_type: int, session: Session = Depends(DbCtrl.get_db_session)):
    NoticeCtrl.deleteNoticesOfType(session, NoticeType(notice_type))
    return CommonResponse()


@router.delete("/{notice_id}", response_model=CommonResponse)
def delete_notice(notice_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    NoticeCtrl.deleteNotice(session, notice_id)
    return CommonResponse()


@router.get("/search/{actor_name}", response_model=UnifiedListResponse[NoticeResponse])
def search_notice(actor_name: str, session: Session = Depends(DbCtrl.get_db_session)):
    notices = NoticeCtrl.searchNotice(session, actor_name)
    return UnifiedListResponse[NoticeResponse](data=notices)

