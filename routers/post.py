from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.params import Body
from Ctrls import DbCtrl, PostCtrl
from routers.schemas import PostResponse
from routers.schemas_others import ActorPostInfo, CommonResponse, UnifiedListResponse
from routers.web_data import PostFilterForm

router = APIRouter(
    prefix="/api/post",
    tags=["post"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/post_count_list", response_model=UnifiedListResponse[ActorPostInfo])
def get_post_count_list(form: PostFilterForm, session: Session = Depends(DbCtrl.get_db_session)):
    post_count_list = PostCtrl.getPostCountList(session, form)
    return UnifiedListResponse[ActorPostInfo](data=post_count_list)


@router.post("/post_list", response_model=UnifiedListResponse[PostResponse])
def get_posts(form: PostFilterForm, session: Session = Depends(DbCtrl.get_db_session)):
    posts = PostCtrl.getFilteredPosts(session, form)
    return UnifiedListResponse[PostResponse](data=posts)


@router.post("/{post_id}/comment", response_model=CommonResponse)
def set_comment(post_id: int, comment: str = Body(default="", media_type="text/plain"), session: Session = Depends(DbCtrl.get_db_session)):
    PostCtrl.setPostComment(session, post_id, comment)
    return CommonResponse()
