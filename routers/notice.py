from fastapi import APIRouter

from Consts import NoticeType
from Ctrls import DbCtrl, NoticeCtrl

router = APIRouter(
    prefix="/api/notice",
    tags=["notice"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get("/count_map")
def get_notice_count():
    with DbCtrl.getSession() as session, session.begin():
        count_map = NoticeCtrl.getNoticeCountMap(session)
        return DbCtrl.CustomJsonResponse(count_map)


@router.get("/list/{notice_type}")
def get_notices(notice_type: int, limit: int = 0, offset: int = 0):
    with DbCtrl.getSession() as session, session.begin():
        notices = NoticeCtrl.getNoticesOfType(session, NoticeType(notice_type), limit, offset)
        return DbCtrl.CustomJsonResponse(notices)


@router.delete("/list/{notice_type}")
def delete_notices(notice_type: int):
    with DbCtrl.getSession() as session, session.begin():
        NoticeCtrl.deleteNoticesOfType(session, NoticeType(notice_type))
        return DbCtrl.CustomJsonResponse({"value": "ok"})


@router.delete("/{notice_id}")
def delete_notice(notice_id: int):
    with DbCtrl.getSession() as session, session.begin():
        NoticeCtrl.deleteNotice(session, notice_id)
        return DbCtrl.CustomJsonResponse({"value": "ok"})
