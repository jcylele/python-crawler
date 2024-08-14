from fastapi import APIRouter

from Ctrls import DbCtrl, ActorTagCtrl
from Models.BaseModel import ActorTagModel
from routers.web_data import ActorTagForm, AllActorTagPriorities

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
        count_map = ActorTagCtrl.getAllTagsUsedCount(session)
        response = []
        for tag in tags:
            json = tag.toJson()
            json['used_count'] = count_map.get(tag.tag_id, 0)
            response.append(json)
        return DbCtrl.CustomJsonResponse(response)


# 必须在/list之后,同方法(get)按顺序匹配
@router.get("/{tag_id}")
def get_actor_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagCtrl.getActorTag(session, tag_id)
        json = tag.toJson()
        json['used_count'] = ActorTagCtrl.getTagUsedCount(session, tag_id)
        return json


# 必须在/list之后,同方法(get)按顺序匹配
@router.delete("/{tag_id}")
def delete_actor_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ActorTagCtrl.deleteActorTag(session, tag_id)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/add")
def add_actor_tag(form: ActorTagForm):
    with DbCtrl.getSession() as session, session.begin():
        tag_group = form.tag_priority // 100
        cur_min_priority = ActorTagCtrl.getMinPriority(session, tag_group)

        tag = ActorTagModel()
        tag.tag_name = form.tag_name
        tag.tag_priority = cur_min_priority - 1
        ActorTagCtrl.addActorTag(session, tag)
        
        return DbCtrl.CustomJsonResponse(tag)


@router.post("/priority")
def update_priorities(form: AllActorTagPriorities):
    with DbCtrl.getSession() as session, session.begin():
        for atp in form.tag_priorities:
            tag = ActorTagCtrl.getActorTag(session, atp.tag_id)
            tag.tag_priority = atp.tag_priority
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.put("/{tag_id}")
def update_actor_tag_name(tag_id: int, tag_name: str):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagCtrl.getActorTag(session, tag_id)
        tag.tag_name = tag_name
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
