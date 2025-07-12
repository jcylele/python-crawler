import subprocess
from typing import List

from fastapi import APIRouter
from fastapi.params import Query

import Configs
from Ctrls import ActorFileCtrl, DbCtrl, ActorCtrl, ActorLogCtrl, ResCtrl, ManualCtrl
from Utils import PyUtil
from routers.web_data import ActorConditionForm, ActorListResult, BatchActorGroup, ActorResult, LinkActorForm

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


@router.get("/group_count")
def get_actor_count_of_groups():
    with DbCtrl.getSession() as session, session.begin():
        actor_count_list = ActorCtrl.getActorCountOfGroups(session)
        return DbCtrl.CustomJsonResponse(actor_count_list)


@router.post("/list")
def get_actor_list(*, form: ActorConditionForm, limit: int, start: int):
    with DbCtrl.getSession() as session, session.begin():
        actor_ids = ActorCtrl.getActorList(session, form, limit, start)
        return DbCtrl.CustomJsonResponse(actor_ids)


@router.post("/finished_list")
def get_finished_actor_list(*, form: ActorConditionForm):
    with DbCtrl.getSession() as session, session.begin():
        actor_ids = ActorCtrl.getFinishedActorList(session, form)
        return DbCtrl.CustomJsonResponse(actor_ids)


@router.post("/link")
def link_actors(form: LinkActorForm):
    # complex logic, ensure transaction is done
    with DbCtrl.getSession() as session, session.begin():
        succeed, msg = ActorCtrl.linkActors(session, form)

    if not succeed:
        return DbCtrl.CustomJsonResponse(ActorListResult(False, msg))

    with DbCtrl.getSession() as session, session.begin():
        actors = [ActorCtrl.getActor(session, actor_id)
                  for actor_id in form.actor_ids]
        return DbCtrl.CustomJsonResponse(ActorListResult(True, msg, actors))


@router.post("/unlink")
def unlink_actors(actor_ids: List[int]):
    with DbCtrl.getSession() as session, session.begin():
        succeed, msg = ActorCtrl.unlinkActors(session, actor_ids)

    if not succeed:
        return DbCtrl.CustomJsonResponse(ActorListResult(False, msg))

    with DbCtrl.getSession() as session, session.begin():
        actors = [ActorCtrl.getActor(session, actor_id)
                  for actor_id in actor_ids]
        return DbCtrl.CustomJsonResponse(ActorListResult(True, msg, actors))


@router.post("/batch/group")
def batch_set_group(form: BatchActorGroup):
    with DbCtrl.getSession() as session, session.begin():
        ar_list = []
        for actor_id in form.actor_ids:
            succeed, actor, msg = ActorCtrl.changeActorGroup(
                session, actor_id, form.group_id)
            ar_list.append(ActorResult(succeed, msg, actor))
        return DbCtrl.CustomJsonResponse(ar_list)


@router.get("/reset_manual")
def reset_manual():
    with DbCtrl.getSession() as session, session.begin():
        ManualCtrl.resetManual(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/similar_names")
def similar_names():
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.findAllSimilarActors(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/clear_group_folder/{group_id}")
def clear_folder_by_group(group_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.getActorsByGroup(session, group_id)
        for actor in actors:
            ActorCtrl.clearActorFolder(session, actor)


# 同方法(get)按顺序匹配, 固定前缀在前，{actor_id}在后, 以下皆为单个匹配

@router.get("/{actor_id}")
def get_actor(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        return DbCtrl.CustomJsonResponse(actor)


@router.patch("/{actor_id}/group")
def change_actor_group(actor_id: int, actor_group_id: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        succeed, actor, msg = ActorCtrl.changeActorGroup(
            session, actor_id, actor_group_id)
        ar = ActorResult(succeed, msg, actor)
        return DbCtrl.CustomJsonResponse(ar)


@router.patch("/{actor_id}/score")
def change_actor_score(actor_id: int, score: int = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.changeActorScore(session, actor_id, score)
        alr = ActorListResult(True, f"actor score changed", actors)
        return DbCtrl.CustomJsonResponse(alr)


@router.patch("/{actor_id}/remark")
def set_actor_remark(actor_id: int, remark: str = Query(alias='val')):
    with DbCtrl.getSession() as session, session.begin():
        real_remark = PyUtil.decodeBase64(remark)
        actors = ActorCtrl.changeActorRemark(session, actor_id, real_remark)
        return DbCtrl.CustomJsonResponse(ActorListResult(True, f"actor remark changed", actors))


@router.post("/{actor_id}/tag")
def change_actor_tag(actor_id: int, tag_list: List[int]):
    with DbCtrl.getSession() as session, session.begin():
        actors = ActorCtrl.changeActorTags(session, actor_id, tag_list)
        return DbCtrl.CustomJsonResponse(ActorListResult(True, f"actor tag changed", actors))


@router.get("/{actor_id}/open")
def open_actor_folder(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        subprocess.Popen(
            f'explorer "{Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)}"')


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


@router.get("/{actor_id}/file_info")
def get_actor_file_info(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ActorCtrl.getActorFileInfo(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_id}/video_stats")
def get_actor_video_stats(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ActorCtrl.getActorVideoStats(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)


@router.get("/{actor_id}/downloading_files")
def get_downloading_files(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        ret = ActorFileCtrl.getDownloadingFilesOfActor(session, actor)
        return DbCtrl.CustomJsonResponse(ret)


@router.delete("/{actor_id}/remove_downloading_files")
def remove_downloading_files(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        ActorFileCtrl.removeDownloadingFilesOfActor(session, actor)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/{actor_id}/rename_files")
def rename_actor_files(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        ActorFileCtrl.rename_actor_files(session, actor)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/{actor_id}/linked")
def get_linked_actors(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actor = ActorCtrl.getActor(session, actor_id)
        if not actor.isLinked():
            return DbCtrl.CustomJsonResponse([actor_id])
        actor_ids = ActorCtrl.getLinkedActorIds(session, actor.main_actor_id)
        return DbCtrl.CustomJsonResponse(actor_ids)


@router.get("/{actor_id}/linked_groups")
def get_linked_groups(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        group_ids = ActorCtrl.getLinkedActorGroups(session, actor_id)
        return DbCtrl.CustomJsonResponse(group_ids)


@router.get("/{actor_id}/logs")
def get_logs(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        logs = ActorLogCtrl.getActorLogs(session, actor_id)
        return DbCtrl.CustomJsonResponse(logs)


@router.get("/{actor_id}/video_sizes")
def get_video_sizes(actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ret = ResCtrl.getResSizesOfActor(session, actor_id)
        return DbCtrl.CustomJsonResponse(ret)
