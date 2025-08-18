from fastapi import APIRouter
from fastapi.params import Body
from Ctrls import DbCtrl, PostCtrl, ResCtrl
from routers.web_data import PostFilterForm

router = APIRouter(
    prefix="/api/post",
    tags=["post"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/post_count_list")
def get_post_count_list(form: PostFilterForm):
    with DbCtrl.getSession() as session, session.begin():
        count_list = PostCtrl.getPostCountList(session, form)
        return DbCtrl.CustomJsonResponse(count_list)


@router.post("/post_list")
def get_posts(form: PostFilterForm):
    with DbCtrl.getSession() as session, session.begin():
        posts = PostCtrl.getFilteredPosts(session, form)
        response = [post for post in posts]
        return DbCtrl.CustomJsonResponse(response)


@router.post("/{post_id}/comment")
def set_comment(post_id: int, comment: str = Body(default="", media_type="text/plain")):
    with DbCtrl.getSession() as session, session.begin():
        PostCtrl.setPostComment(session, post_id, comment)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
