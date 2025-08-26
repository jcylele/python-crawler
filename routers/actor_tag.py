from typing import TypeAlias
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.params import Body

from Consts import ErrorCode
from Ctrls import DbCtrl, ActorTagCtrl
from Models.ActorTagModel import ActorTagModel
from routers.schemas import ActorTagFullResponse, ActorTagResponse
from routers.schemas_others import CommonResponse, UnifiedResponse
from routers.web_data import ActorTagForm, CommonPriority, TagUsedInfo

router = APIRouter(
    prefix="/api/actor_tag",
    tags=["actor_tag"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

ActorTagFullResult: TypeAlias = UnifiedResponse[ActorTagFullResponse]

def _format_full_tag(tag: ActorTagModel, used_info: TagUsedInfo | None = None) -> ActorTagFullResponse:
    base_tag_data = ActorTagResponse.model_validate(tag)
    if used_info is None:
        return ActorTagFullResponse(
            **base_tag_data.model_dump(),
            used_count=0,
            avg_score=0
        )
    return ActorTagFullResponse(
        **base_tag_data.model_dump(),
        **used_info.model_dump()
    )


@router.get("/list", response_model=UnifiedResponse[list[ActorTagFullResponse]])
def get_actor_tag_list(session: Session = Depends(DbCtrl.get_db_session)):
    tags = ActorTagCtrl.getAllActorTags(session)
    used_info_map = ActorTagCtrl.getAllTagsUsedInfo(session)
    full_tag_list = []
    for tag in tags:
        used_info = used_info_map.get(tag.tag_id)
        full_tag_list.append(_format_full_tag(tag, used_info))
    return UnifiedResponse[list[ActorTagFullResponse]](data=full_tag_list)


@router.post("/add", response_model=UnifiedResponse[ActorTagResponse])
def add_actor_tag(form: ActorTagForm, session: Session = Depends(DbCtrl.get_db_session)):
    tag = ActorTagModel()
    tag.tag_name = form.tag_name
    tag.tag_priority = form.tag_priority
    tag = ActorTagCtrl.addActorTag(session, tag)
    return UnifiedResponse[ActorTagResponse](data=tag)


@router.post("/priority", response_model=CommonResponse)
def update_priorities(priority_list: list[CommonPriority], session: Session = Depends(DbCtrl.get_db_session)):
    for p in priority_list:
        tag = ActorTagCtrl.getActorTag(session, p.id)
        tag.tag_priority = p.priority
    return CommonResponse()

# 必须在/list之后,同方法(get)按顺序匹配


@router.get("/{tag_id}", response_model=ActorTagFullResult)
def get_actor_tag(tag_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    tag = ActorTagCtrl.getActorTag(session, tag_id)
    if tag is None:
        return ActorTagFullResult(error_code=ErrorCode.TagNotFound)
    used_info = ActorTagCtrl.getTagUsedInfo(session, tag_id)
    return ActorTagFullResult(data=_format_full_tag(tag, used_info))


# 必须在/list之后,同方法(get)按顺序匹配
@router.delete("/{tag_id}", response_model=CommonResponse)
def delete_actor_tag(tag_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorTagCtrl.deleteActorTag(session, tag_id)
    return CommonResponse()


@router.post("/{tag_id}/name", response_model=CommonResponse)
def update_actor_tag_name(tag_id: int, tag_name: str = Body(media_type="text/plain"), session: Session = Depends(DbCtrl.get_db_session)):
    ActorTagCtrl.setTagName(session, tag_id, tag_name)
    return CommonResponse()
