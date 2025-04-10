from fastapi import APIRouter

from Ctrls import DbCtrl, ActorTagCtrl
from Models.ActorTagModel import ActorTagModel
from routers.web_data import ActorTagForm, AllActorTagPriorities, TagUsedInfo

router = APIRouter(
    prefix="/api/actor_tag",
    tags=["actor_tag"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


def format_tag_json(tag: ActorTagModel, used_info: TagUsedInfo) -> dict:
    json = tag.toJson()
    if used_info is None:
        json['used_count'] = 0
        json['avg_score'] = 0
    else:
        for k, v in used_info.items():
            json[k] = v
    return json


@router.get("/list")
def get_actor_tag_list():
    with DbCtrl.getSession() as session, session.begin():
        tags = ActorTagCtrl.getAllActorTags(session)
        used_info_map = ActorTagCtrl.getAllTagsUsedInfo(session)
        response = []
        for tag in tags:
            used_info = used_info_map.get(tag.tag_id)
            json = format_tag_json(tag, used_info)
            response.append(json)
        return DbCtrl.CustomJsonResponse(response)


# 必须在/list之后,同方法(get)按顺序匹配
@router.get("/{tag_id}")
def get_actor_tag(tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        tag = ActorTagCtrl.getActorTag(session, tag_id)
        used_info = ActorTagCtrl.getTagUsedInfo(session, tag_id)
        json = format_tag_json(tag, used_info)
        return DbCtrl.CustomJsonResponse(json)


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
        ActorTagCtrl.setTagName(session, tag_id, tag_name)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
