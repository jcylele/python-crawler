import threading

from fastapi import APIRouter

from Ctrls import DbCtrl, ActorCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks
from routers.web_data import CategoryDownloadForm, NameDownloadForm, UrlDownloadForm

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/clean")
def cleanFiles():
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.removeOutdatedFiles(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/new")
def download_new_actors(form: CategoryDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitCategory(form.actor_category)
    task.downloadNewActors()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/category")
def download_by_category(form: CategoryDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.downloadByActorCategory(form.actor_category)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


def add_task(actor_name: str, download_limit: DownloadLimit):
    limit = DownloadLimit(download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.downloadSpecificActor(actor_name)


@router.post("/specific")
def download_specific(form: NameDownloadForm):
    for actor_name in form.actor_names:
        x = threading.Thread(target=add_task, args=(actor_name, form.download_limit,))
        x.start()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/urls")
def download_by_urls(form: UrlDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitCategory(form.actor_category)
    task.downloadByUrls(form.urls)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/list")
def get_tasks():
    tasks = GetAllTask()
    return DbCtrl.CustomJsonResponse(tasks)


# must before @router.delete("/{task_uid}")
@router.delete("/all")
def stop_all_task():
    StopAllTasks()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.delete("/{task_uid}")
def stop_task(task_uid: int):
    StopTask(task_uid)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})
