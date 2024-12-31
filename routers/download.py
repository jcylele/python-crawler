import threading

from fastapi import APIRouter

from Ctrls import DbCtrl, ActorCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks, GetActorIds
from routers.web_data import GroupDownloadForm, ActorIdDownloadForm, UrlDownloadForm, BaseDownloadForm

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/new")
def download_new_actors(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadNewActors()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/group")
def download_by_group(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.downloadByActorGroup(form.actor_group_id)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/resume")
def resume_files(form: BaseDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.resumeFiles()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


def add_task(actor_id: str, download_limit: DownloadLimit):
    limit = DownloadLimit(download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.downloadSpecificActor(actor_id)


@router.post("/specific")
def download_specific(form: ActorIdDownloadForm):
    for actor_id in form.actor_ids:
        x = threading.Thread(target=add_task, args=(actor_id, form.download_limit,))
        x.start()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/urls")
def download_by_urls(form: UrlDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadByUrls(form.urls)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/list")
def get_tasks():
    tasks = GetAllTask()
    return DbCtrl.CustomJsonResponse(tasks)


@router.get("/actor_ids")
def get_task_actor_ids():
    actor_ids = GetActorIds()
    return DbCtrl.CustomJsonResponse(actor_ids)


# must before @router.delete("/{task_uid}")
@router.delete("/all")
def stop_all_task():
    StopAllTasks()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.delete("/{task_uid}")
def stop_task(task_uid: int):
    StopTask(task_uid)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/clean")
def cleanFiles():
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.removeOutdatedFiles(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})
