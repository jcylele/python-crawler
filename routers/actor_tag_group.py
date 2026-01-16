from typing import TypeAlias
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Ctrls import ActorTagGroupCtrl, DbCtrl
from routers.schemas import ActorTagGroupResponse
from routers.schemas_others import CommonResponse, UnifiedResponse
from routers.web_data import CommonGroupForm, CommonPriority

router = APIRouter(
    prefix="/api/actor_tag_group",
    tags=["actor_tag_group"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

ActorTagGroupResult: TypeAlias = UnifiedResponse[ActorTagGroupResponse]


@router.get("/list", response_model=UnifiedResponse[list[ActorTagGroupResponse]])
def get_actor_tag_group_list(session: Session = Depends(DbCtrl.get_db_session)):
    actor_tag_groups = ActorTagGroupCtrl.getAllActorTagGroups(session)
    return UnifiedResponse[list[ActorTagGroupResponse]](data=actor_tag_groups)


@router.post("/add", response_model=ActorTagGroupResult)
def add_actor_tag_group(form: CommonGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    actor_tag_group = ActorTagGroupCtrl.addNewActorTagGroup(session, form)
    return ActorTagGroupResult(data=actor_tag_group)


@router.post("/priority", response_model=CommonResponse)
def update_priorities(priority_list: list[CommonPriority], session: Session = Depends(DbCtrl.get_db_session)):
    for p in priority_list:
        group = ActorTagGroupCtrl.getActorTagGroup(session, p.id)
        group.group_priority = p.priority
    return CommonResponse()


@router.get("/{group_id}", response_model=ActorTagGroupResult)
def get_actor_tag_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_tag_group = ActorTagGroupCtrl.getActorTagGroup(session, group_id)
    return ActorTagGroupResult(data=actor_tag_group)


@router.post("/{group_id}/update", response_model=ActorTagGroupResult)
def update_actor_tag_group(group_id: int, form: CommonGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    actor_tag_group = ActorTagGroupCtrl.updateActorTagGroup(
        session, group_id, form)
    return ActorTagGroupResult(data=actor_tag_group)


@router.delete("/{group_id}", response_model=CommonResponse)
def delete_actor_tag_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorTagGroupCtrl.deleteActorTagGroup(session, group_id)
    return CommonResponse()


@router.patch("/{group_id}/add_tag/{tag_id}", response_model=CommonResponse)
def add_tag_to_actor_tag_group(group_id: int, tag_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorTagGroupCtrl.addTagToGroup(session, group_id, tag_id)
    return CommonResponse()


@router.patch("/{group_id}/remove_tag/{tag_id}", response_model=CommonResponse)
def remove_tag_from_actor_tag_group(group_id: int, tag_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorTagGroupCtrl.removeTagFromGroup(
        session, group_id, tag_id)
    return CommonResponse()
