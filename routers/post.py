from fastapi import APIRouter

from Ctrls import DbCtrl, PostCtrl
from Utils import LogUtil
from routers.web_data import PostConditionForm, PostCommentForm

router = APIRouter(
    prefix="/api/post",
    tags=["post"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/actor_list")
def get_actors(form: PostConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        actor_list = PostCtrl.getFilteredActors(session, form)
        print(actor_list)
        return DbCtrl.CustomJsonResponse(actor_list)


@router.post("/post_list")
def get_posts(form: PostConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        posts = PostCtrl.getFilteredPosts(session, form)
        response = []
        for post in posts:
            json = post.toJson()
            response.append(json)
        LogUtil.info(f"{form} get {len(response)} posts")
        return DbCtrl.CustomJsonResponse(response)


@router.post("/set_comment")
def set_comment(form: PostCommentForm):
    with DbCtrl.getSession() as session, session.begin():
        PostCtrl.setPostComment(session, form)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
