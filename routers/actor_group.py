from fastapi import APIRouter

from Ctrls import DbCtrl, ActorGroupCtrl
from routers.web_data import ActorGroupForm

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


@router.get("/{group_id}")
def get_actor_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.getActorGroup(session, group_id)
        return DbCtrl.CustomJsonResponse(group)


@router.post("/add")
def add_actor_group(form: ActorGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.addNewActorGroup(session, form)
        return DbCtrl.CustomJsonResponse(group)


@router.post("/update")
def update_actor_group(form: ActorGroupForm):
    with DbCtrl.getSession() as session, session.begin():
        group = ActorGroupCtrl.updateActorGroup(session, form)
        return DbCtrl.CustomJsonResponse(group)


@router.delete("/{group_id}")
def delete_actor_tag(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        succeed = ActorGroupCtrl.deleteActorGroup(session, group_id)
        return DbCtrl.CustomJsonResponse({'value': succeed})
