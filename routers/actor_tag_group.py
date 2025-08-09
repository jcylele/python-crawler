from fastapi import APIRouter

from Ctrls import ActorTagGroupCtrl, DbCtrl
from routers.web_data import CommonGroupForm, CommonPriority

router = APIRouter(
    prefix="/api/actor_tag_group",
    tags=["actor_tag_group"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/list")
def get_actor_tag_group_list():
    with DbCtrl.getSession() as session, session.begin():
        groups = ActorTagGroupCtrl.getAllActorTagGroups(session)
        response = []
        for group in groups:
            response.append(group)
        return DbCtrl.CustomJsonResponse(response)

@router.post("/add")
def add_actor_tag_group(form: CommonGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorTagGroupCtrl.addNewActorTagGroup(session, form)
        return DbCtrl.CustomJsonResponse(group)

@router.post("/priority")
def update_priorities(priority_list: list[CommonPriority]):
    with DbCtrl.getSession() as session, session.begin():
        for p in priority_list:
            group = ActorTagGroupCtrl.getActorTagGroup(session, p.id)
            group.group_priority = p.priority
        return DbCtrl.CustomJsonResponse({'value': True})

@router.get("/{group_id}")
def get_actor_tag_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorTagGroupCtrl.getActorTagGroup(session, group_id)
        return DbCtrl.CustomJsonResponse(group)

@router.post("/{group_id}/update")
def update_actor_tag_group(group_id: int, form: CommonGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorTagGroupCtrl.updateActorTagGroup(session, group_id, form)
        return DbCtrl.CustomJsonResponse(group)


@router.delete("/{group_id}")
def delete_actor_tag_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        succeed = ActorTagGroupCtrl.deleteActorTagGroup(session, group_id)
        return DbCtrl.CustomJsonResponse({'value': succeed})


@router.patch("/{group_id}/add_tag/{tag_id}")
def add_tag_to_actor_tag_group(group_id: int, tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        succeed = ActorTagGroupCtrl.addTagToGroup(session, group_id, tag_id)
        return DbCtrl.CustomJsonResponse({'value': succeed})


@router.patch("/{group_id}/remove_tag/{tag_id}")
def remove_tag_from_actor_tag_group(group_id: int, tag_id: int):
    with DbCtrl.getSession() as session, session.begin():
        succeed = ActorTagGroupCtrl.removeTagFromGroup(
            session, group_id, tag_id)
        return DbCtrl.CustomJsonResponse({'value': succeed})
