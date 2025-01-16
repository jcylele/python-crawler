import base64
import subprocess
from typing import List

from fastapi import APIRouter
from fastapi.params import Query

import Configs
from Ctrls import DbCtrl, ActorCtrl, ActorLogCtrl, ResCtrl
from routers.web_data import ActorConditionForm, BatchActorGroup

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
def link_actors(actor_ids: List[int]):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.linkActors(session, actor_ids)
        return DbCtrl.CustomJsonResponse(actors)


@router.post("/unlink")
def unlink_actors(actor_ids: List[int]):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.unlinkActors(session, actor_ids)
        return DbCtrl.CustomJsonResponse(actors)


@router.post("/batch/group")
def batch_set_group(form: BatchActorGroup):
    with DbCtrl.getSession() as session, session.begin():
        actors = []
        for actor_id in form.actor_ids:
            actor = ActorCtrl.changeActorGroup(session, actor_id, form.group_id)
            actors.append(actor)
        return DbCtrl.CustomJsonResponse(actors)


# 同方法(get)按顺序匹配, 固定前缀在前，{actor_name}在后

@router.get("/{actor_id}")
def get_actor(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_id}/group")
def change_actor_category(actor_id: int, actor_group_id: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorGroup(session, actor_id, actor_group_id)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_id}/score")
def change_actor_category(actor_id: int, score: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorScore(session, actor_id, score)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_id}/remark")
def set_actor_remark(actor_id: int, remark: str = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        remark += '=='
        real_remark = base64.urlsafe_b64decode(remark).decode('utf-8')
        actor = ActorCtrl.changeActorRemark(session, actor_id, real_remark)
        return DbCtrl.CustomJsonResponse(actor)


@router.get("/{actor_id}/open")
def open_actor_folder(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        subprocess.Popen(f'explorer "{Configs.formatActorFolderPath(actor.actor_name)}"')


@router.patch("/{actor_id}/reset_posts")
def reset_actor_posts(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.ResetActorPosts(session, actor_id)
        session.flush()
        ret = ActorCtrl.getActorFileInfo(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_id}/clear")
def clear_actor_folder(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        ActorCtrl.clearActorFolder(session, actor)
        session.flush()
        ret = ActorCtrl.getActorFileInfo(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.post("/{actor_id}/tag")
def change_actor_tag(actor_id: int, tag_list: List[int]):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.changeActorTags(session, actor_id, tag_list)
        return DbCtrl.CustomJsonResponse(actor)


@router.get("/{actor_id}/file_info")
def get_actor_file_info(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ActorCtrl.getActorFileInfo(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_id}/linked")
def get_linked_actors(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.getLinkedActors(session, actor_id)
        return DbCtrl.CustomJsonResponse(actors)


@router.get("/{actor_id}/logs")
def get_logs(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        logs = ActorLogCtrl.getActorLogs(session, actor_id)
        return DbCtrl.CustomJsonResponse(logs)


@router.get("/{actor_id}/video_states")
def get_video_states(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ResCtrl.getResStatesOfActor(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_id}/video_sizes")
def get_video_sizes(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ResCtrl.getResSizesOfActor(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)
