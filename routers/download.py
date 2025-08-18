import os
import threading
import subprocess

from fastapi import APIRouter

from Consts import CacheKey
from Ctrls import ActorFileCtrl, DbCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks, GetActorIds, GetTaskCount
from Utils import CacheUtil
from routers.web_data import GroupDownloadForm, ActorIdDownloadForm, UrlDownloadForm, \
    NewDownloadForm, DownloadLimitForm

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/custom_page")
def get_custom_page():
    page = CacheUtil.getValue(CacheKey.CustomPage)
    return DbCtrl.CustomJsonResponse(page)


@router.post("/new")
def download_new_actors(form: NewDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadNewActors(form.start_page)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/group")
def download_by_group(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadByActorGroup(form.actor_group_id)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})

@router.patch("/resume/{actor_id}")
def resume_actor(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.resumeVideoLimit())
    task = NewTask()
    task.setLimit(limit)
    task.resumeActor(actor_id)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})

@router.patch("/fix_posts/{actor_id}")
def fix_posts(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.fixPostsLimit())
    task = NewTask()
    task.setLimit(limit)
    task.fix_posts_of_actor(actor_id)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})

@router.post("/manual")
def manual(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.manual()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


def add_task(actor_id: int, download_limit: DownloadLimitForm):
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


@router.get("/count")
def get_task_count():
    count = GetTaskCount()
    return DbCtrl.CustomJsonResponse(count)


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
        ActorFileCtrl.removeOutdatedFiles(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/logs")
def openLogFolder():
    cur_dir = os.getcwd()
    subprocess.Popen(f'explorer {cur_dir}\\logs')
