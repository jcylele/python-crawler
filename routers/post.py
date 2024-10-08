from fastapi import APIRouter
from Ctrls import DbCtrl, PostCtrl
from routers.web_data import PostConditionForm, PostCommentForm

router = APIRouter(
    prefix="/api/post",
    tags=["post"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/post_count_list")
def get_post_count_list(form: PostConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        count_list = PostCtrl.getPostCountList(session, form)
        return DbCtrl.CustomJsonResponse(count_list)


@router.post("/post_list")
def get_posts(form: PostConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        posts = PostCtrl.getFilteredPosts(session, form)
        response = [post for post in posts]
        return DbCtrl.CustomJsonResponse(response)


@router.post("/set_comment")
def set_comment(form: PostCommentForm):
    with DbCtrl.getSession() as session, session.begin():
        PostCtrl.setPostComment(session, int(form.post_id), form.comment)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
