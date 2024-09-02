from fastapi import APIRouter
from fastapi.params import Query
from Ctrls import ChartCtrl, DbCtrl

router = APIRouter(
    prefix="/api/chart",
    tags=["chart"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/relative_of_tag/{tag_id}")
def relative_of_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        count_map = ChartCtrl.getTagRelative(session, tag_id)
        return DbCtrl.CustomJsonResponse(count_map)


@router.get("/scores_of_tag/{tag_id}")
def scores_of_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        scores = ChartCtrl.getScoresByTag(session, tag_id)
        return DbCtrl.CustomJsonResponse(scores)


@router.get("/tags_of_score")
def tags_of_score(min_score: int = Query(alias='min'), max_score: int = Query(alias='max')):
    with DbCtrl.getSession() as session, session.begin():
        tags = ChartCtrl.getTagsByScore(session, min_score, max_score)
        return DbCtrl.CustomJsonResponse(tags)
