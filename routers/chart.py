from typing import List

from fastapi import APIRouter
from fastapi.params import Query
from Ctrls import ChartCtrl, DbCtrl

router = APIRouter(
    prefix="/api/chart",
    tags=["chart"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/relative_of_tag")
def relative_of_tag(tag_id: int = Query(alias='id'), limit: int = Query()):
    with DbCtrl.getSession() as session, session.begin():
        count_map = ChartCtrl.getTagRelative(session, tag_id, limit)
        return DbCtrl.CustomJsonResponse(count_map)


@router.post("/scores_of_tag")
def scores_of_tag(tag_ids: List[int]):
    ret = []
    with DbCtrl.getSession() as session, session.begin():
        for tag_id in tag_ids:
            scores = ChartCtrl.getScoresByTag(session, tag_id)
            ret.append(scores)
    return DbCtrl.CustomJsonResponse(ret)


@router.get("/tags_of_score")
def tags_of_score(min_score: int = Query(alias='min'), max_score: int = Query(alias='max'), limit: int = Query()):
    with DbCtrl.getSession() as session, session.begin():
        tags = ChartCtrl.getTagCountsByScore(session, min_score, max_score, limit)
        return DbCtrl.CustomJsonResponse(tags)

@router.get("/down_size_of_groups")
def down_size_of_groups():
    with DbCtrl.getSession() as session, session.begin():
        ret = ChartCtrl.getResSizeStats(session)
        return DbCtrl.CustomJsonResponse(ret)