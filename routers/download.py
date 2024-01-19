from fastapi import APIRouter
from fastapi.params import Query

from Ctrls import DbCtrl, ActorCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks
from Models.BaseModel import ActorCategory
from routers.web_data import DownloadLimitForm

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/restore")
def restoreRecord():
    with DbCtrl.getSession() as session, session.begin():
        ActorCtrl.removeDownloadingFiles(session)
        return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/new")
def download_new_actors(form: DownloadLimitForm):
    limit = DownloadLimit(form)
    task = NewTask()
    task.setLimit(limit)
    task.downloadNewActors()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/category/{actor_category}")
def download_by_category(actor_category: int, form: DownloadLimitForm):
    limit = DownloadLimit(form)
    task = NewTask()
    task.setLimit(limit)
    task.downloadByActorCategory(ActorCategory(actor_category))
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/specific")
def download_by_category(form: DownloadLimitForm, names: list[str] = Query(alias='name')):
    limit = DownloadLimit(form)
    task = NewTask()
    task.setLimit(limit)
    task.downloadSpecificActors(names)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.get("/list")
def get_tasks():
    tasks = GetAllTask()
    return DbCtrl.CustomJsonResponse(tasks)


# must before stop_task
@router.delete("/all")
def stop_all_task():
    StopAllTasks()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.delete("/{task_uid}")
def stop_task(task_uid: int):
    StopTask(task_uid)
    return DbCtrl.CustomJsonResponse({'value': 'ok'})
