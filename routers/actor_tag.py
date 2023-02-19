from fastapi import APIRouter
from pydantic import BaseModel

from Ctrls import DbCtrl, ActorTagCtrl
from Models.BaseModel import ActorTagModel

router = APIRouter(
    prefix="/api/actor_tag",
    tags=["actor_tag"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/list")
def get_actor_tag_list():
    with DbCtrl.getSession() as session, session.begin():
        tags = ActorTagCtrl.getAllActorTags(session)
        response = []
        for tag in tags:
            response.append(tag)
        return DbCtrl.CustomJsonResponse(response)


# 必须在/list之后,同方法(get)按顺序匹配
@router.get("/{tag_id}")
def get_actor_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagCtrl.getActorTag(session, tag_id)
        return DbCtrl.CustomJsonResponse(tag)


class ActorTagForm(BaseModel):
    tag_name: str
    tag_priority: int


@router.post("/add")
def add_actor_tag(tag_form: ActorTagForm):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagModel()
        tag.__dict__.update(tag_form.__dict__)
        ActorTagCtrl.addActorTag(session, tag)
        return DbCtrl.CustomJsonResponse(tag)


@router.put("/{tag_id}")
def put_actor_tag(tag_id: int, tag_form: ActorTagForm):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagCtrl.getActorTag(session, tag_id)
        tag.tag_name = tag_form.tag_name
        tag.tag_priority = tag_form.tag_priority
        session.flush()
        return DbCtrl.CustomJsonResponse(tag)


@router.delete("/{tag_id}")
def delete_actor_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        tag_name = ActorTagCtrl.deleteActorTag(session, tag_id)
        return DbCtrl.CustomJsonResponse({"value": tag_name})
