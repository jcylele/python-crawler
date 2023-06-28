import subprocess
from typing import List

from fastapi import APIRouter
from fastapi.params import Query

import Configs
from Ctrls import DbCtrl, ActorCtrl, FileInfoCacheCtrl
from Models.BaseModel import ActorCategory
from routers.web_data import ActorConditionForm

router = APIRouter(
    prefix="/api/actor",
    tags=["actor"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/count")
def get_actor_count(form: ActorConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        actor_count = ActorCtrl.getActorCount(session, form)
        return DbCtrl.CustomJsonResponse({'value': actor_count})


@router.post("/list")
def get_actor_list(*, form: ActorConditionForm, limit: int, start: int):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.getActorList(session, form, limit, start)

        response = []
        for actor in actors:
            response.append(actor)
        return DbCtrl.CustomJsonResponse(response)


# 必须在/list和/count之后,同方法(get)按顺序匹配
@router.get("/{actor_name}")
def get_actor(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_name)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_name}/category")
def change_actor_category(actor_name: str, actor_category: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorCategory(session, actor_name, ActorCategory(actor_category))
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_name}/star")
def change_actor_category(actor_name: str, star: bool = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorStar(session, actor_name, star)
        return DbCtrl.CustomJsonResponse(actor)


@router.get("/{actor_name}/open")
def get_actor(actor_name: str):
    subprocess.Popen(f'explorer "{Configs.formatActorFolderPath(actor_name)}"')


@router.post("/{actor_name}/tag")
def change_actor_tag(actor_name: str, tag_list: List[int] = Query(alias='id')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorTags(session, actor_name, tag_list)
        return DbCtrl.CustomJsonResponse(actor)
