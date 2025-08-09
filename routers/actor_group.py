from fastapi import APIRouter

from Ctrls import DbCtrl, ActorGroupCtrl
from routers.web_data import ActorGroupForm, ActorGroupCond, CommonPriority

router = APIRouter(
    prefix="/api/actor_group",
    tags=["actor_group"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/list")
def get_actor_group_list():
    with DbCtrl.getSession() as session, session.begin():
        groups = ActorGroupCtrl.getAllActorGroups(session)
        response = []
        for group in groups:
            response.append(group)
        return DbCtrl.CustomJsonResponse(response)


@router.post("/add")
def add_actor_group(form: ActorGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.addNewActorGroup(session, form)
        return DbCtrl.CustomJsonResponse(group)


@router.post("/priority")
def update_priorities(priority_list: list[CommonPriority]):
    with DbCtrl.getSession() as session, session.begin():
        for p in priority_list:
            group = ActorGroupCtrl.getActorGroup(session, p.id)
            group.group_priority = p.priority
        return DbCtrl.CustomJsonResponse({'value': True})


@router.get("/{group_id}")
def get_actor_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.getActorGroup(session, group_id)
        return DbCtrl.CustomJsonResponse(group)


@router.post("/{group_id}/update")
def update_actor_group(group_id: int, form: ActorGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.updateActorGroup(session, group_id, form)
        return DbCtrl.CustomJsonResponse(group)


@router.delete("/{group_id}")
def delete_actor_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        succeed = ActorGroupCtrl.deleteActorGroup(session, group_id)
        return DbCtrl.CustomJsonResponse({'value': succeed})


@router.post("/{group_id}/set_condition")
def set_group_condition(group_id: int, cond_list: list[ActorGroupCond]):
    with DbCtrl.getSession() as session, session.begin():
        ActorGroupCtrl.setGroupCondition(session, group_id, cond_list)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
