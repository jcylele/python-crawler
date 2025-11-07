
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.params import Query
from Consts import DateFormat
from Ctrls import ChartCtrl, DbCtrl, ResFileCtrl
from Utils import PyUtil
from routers.schemas_others import GroupTimeStats, TagCount, DownloadingVideoStats, UnifiedListResponse, UnifiedResponse
from routers.web_data import GroupTimeStatsForm

router = APIRouter(
    prefix="/api/chart",
    tags=["chart"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/relative_of_tag", response_model=UnifiedListResponse[TagCount])
def relative_of_tag(tag_id: int = Query(alias='id'), limit: int = Query(), session: Session = Depends(DbCtrl.get_db_session)):
    tag_relative = ChartCtrl.getTagRelative(session, tag_id, limit)
    return UnifiedListResponse[TagCount](data=tag_relative)


@router.post("/scores_of_tag", response_model=UnifiedResponse[list[list[int]]])
def scores_of_tag(tag_ids: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    scores_of_tag = list(
        map(lambda tag_id: ChartCtrl.getScoresByTag(session, tag_id), tag_ids))
    return UnifiedResponse[list[list[int]]](data=scores_of_tag)


@router.get("/tags_of_score", response_model=UnifiedListResponse[TagCount])
def tags_of_score(min_score: int = Query(alias='min'), max_score: int = Query(alias='max'), limit: int = Query(), session: Session = Depends(DbCtrl.get_db_session)):
    tags_of_score = ChartCtrl.getTagCountsByScore(
        session, min_score, max_score, limit)
    return UnifiedListResponse[TagCount](data=tags_of_score)


@router.get("/down_size_of_groups", response_model=UnifiedResponse[dict[int, int]])
def down_size_of_groups(session: Session = Depends(DbCtrl.get_db_session)):
    down_size_of_groups = ChartCtrl.getResSizeStats(session)
    down_size_of_groups[0] = ResFileCtrl.getTotalDownloadingSize(session)
    # type: ignore
    return UnifiedResponse[dict[int, int]](data=down_size_of_groups)


@router.get("/downloading_video_stats", response_model=UnifiedListResponse[DownloadingVideoStats])
def downloading_video_stats(session: Session = Depends(DbCtrl.get_db_session)):
    downloading_video_stats = ResFileCtrl.get_downloading_video_stats(session)
    return UnifiedListResponse[DownloadingVideoStats](data=downloading_video_stats)


@router.post("/actor_group_time_stats", response_model=UnifiedListResponse[GroupTimeStats])
def actor_group_time_stats(form: GroupTimeStatsForm, session: Session = Depends(DbCtrl.get_db_session)):
    start_date = PyUtil.to_date(form.start_date, DateFormat.Date, True)
    end_date = PyUtil.to_date(form.end_date, DateFormat.Date, False)
    actor_group_time_stats = ChartCtrl.get_actor_group_time_stats(
        session, start_date, end_date, form.group_ids)
    return UnifiedListResponse[GroupTimeStats](data=actor_group_time_stats)
