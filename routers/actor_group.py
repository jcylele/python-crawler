from typing import TypeAlias
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Consts import ErrorCode
from Ctrls import DbCtrl, ActorGroupCtrl
from routers.schemas import ActorGroupResponse
from routers.schemas_others import CommonResponse, UnifiedResponse
from routers.web_data import ActorGroupForm, ActorGroupCond, CommonPriority

router = APIRouter(
    prefix="/api/actor_group",
    tags=["actor_group"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

ActorGroupResult: TypeAlias = UnifiedResponse[ActorGroupResponse]

@router.get("/list", response_model=UnifiedResponse[list[ActorGroupResponse]])
def get_actor_group_list(session: Session = Depends(DbCtrl.get_db_session)):
    actor_groups = ActorGroupCtrl.getAllActorGroups(session)
    return UnifiedResponse[list[ActorGroupResponse]](data=actor_groups) 


@router.post("/add", response_model=ActorGroupResult)
def add_actor_group(form: ActorGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    actor_group = ActorGroupCtrl.addNewActorGroup(session, form)
    return ActorGroupResult(data=actor_group)


@router.post("/priority", response_model=CommonResponse)
def update_priorities(priority_list: list[CommonPriority], session: Session = Depends(DbCtrl.get_db_session)):
    for p in priority_list:
        group = ActorGroupCtrl.getActorGroup(session, p.id)
        group.group_priority = p.priority
    return CommonResponse()


@router.get("/{group_id}", response_model=ActorGroupResult)
def get_actor_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_group = ActorGroupCtrl.getActorGroup(session, group_id)
    if actor_group is None:
        return ActorGroupResult(error_code=ErrorCode.ActorGroupNotFound)
    return ActorGroupResult(data=actor_group)


@router.post("/{group_id}/update", response_model=ActorGroupResult)
def update_actor_group(group_id: int, form: ActorGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    actor_group = ActorGroupCtrl.updateActorGroup(session, group_id, form)
    return ActorGroupResult(data=actor_group)


@router.delete("/{group_id}", response_model=CommonResponse)
def delete_actor_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    error_code = ActorGroupCtrl.deleteActorGroup(session, group_id)
    return CommonResponse(error_code=error_code)


@router.post("/{group_id}/set_condition", response_model=CommonResponse)
def set_group_condition(group_id: int, cond_list: list[ActorGroupCond], session: Session = Depends(DbCtrl.get_db_session)):
    ActorGroupCtrl.setGroupCondition(session, group_id, cond_list)
    return CommonResponse()
