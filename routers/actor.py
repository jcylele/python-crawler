import base64
import subprocess
from typing import List

from fastapi import APIRouter
from fastapi.params import Query

import Configs
from Ctrls import DbCtrl, ActorCtrl, FileInfoCacheCtrl, PostCtrl
from routers.web_data import ActorConditionForm, BatchActorCategory

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


@router.post("/link")
def link_actors(actor_names: List[str]):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.linkActors(session, actor_names)
        return DbCtrl.CustomJsonResponse(actors)


@router.post("/batch/category")
def batch_set_category(form: BatchActorCategory):
    with DbCtrl.getSession() as session, session.begin():
        actors = []
        for actor_name in form.actor_names:
            actor = ActorCtrl.changeActorCategory(session, actor_name, form.category)
            actors.append(actor)
        return DbCtrl.CustomJsonResponse(actors)


# 同方法(get)按顺序匹配, 固定前缀在前，{actor_name}在后

@router.get("/{actor_name}")
def get_actor(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_name)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_name}/category")
def change_actor_category(actor_name: str, actor_category: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorCategory(session, actor_name, actor_category)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_name}/score")
def change_actor_category(actor_name: str, score: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorScore(session, actor_name, score)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_name}/remark")
def set_actor_remark(actor_name: str, remark: str = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        remark += '=='
        real_remark = base64.urlsafe_b64decode(remark).decode('utf-8')
        actor = ActorCtrl.changeActorRemark(session, actor_name, real_remark)
        return DbCtrl.CustomJsonResponse(actor)


@router.get("/{actor_name}/open")
def open_actor_folder(actor_name: str):
    subprocess.Popen(f'explorer "{Configs.formatActorFolderPath(actor_name)}"')


@router.get("/{actor_name}/reset_posts")
def reset_actor_posts(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.ResetActorPosts(session, actor_name)
        session.flush()
        ret = ActorCtrl.getActorFileInfo(session, actor_name)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_name}/clear")
def clear_actor_folder(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.clearActorFolder(session, actor_name);
        session.flush()
        ret = ActorCtrl.getActorFileInfo(session, actor_name)
        return DbCtrl.CustomJsonResponse(ret)


@router.post("/{actor_name}/tag")
def change_actor_tag(actor_name: str, tag_list: List[int] = Query(alias='id')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorTags(session, actor_name, tag_list)
        return DbCtrl.CustomJsonResponse(actor)


@router.get("/{actor_name}/file_info")
def get_actor_file_info(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        ret = ActorCtrl.getActorFileInfo(session, actor_name)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_name}/link")
def get_linked_actors(actor_name: str):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.getLinkedActors(session, actor_name)
        return DbCtrl.CustomJsonResponse(actors)
