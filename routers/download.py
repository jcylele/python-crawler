import os
import threading
import subprocess

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Consts import CacheKey
from Ctrls import ActorFileCtrl, DbCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks, GetActorIds, GetTaskCount
from Utils import CacheUtil
from routers.web_data import GroupDownloadForm, ActorIdDownloadForm, UrlDownloadForm, \
    NewDownloadForm, DownloadLimitForm
from routers.schemas_others import CommonResponse, DownloadTaskResponse, UnifiedListResponse, UnifiedResponse

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/custom_page", response_model=UnifiedResponse[int])
def get_custom_page():
    page: int = CacheUtil.getValue(CacheKey.CustomPage)
    return UnifiedResponse[int](data=page)


@router.post("/new", response_model=CommonResponse)
def download_new_actors(form: NewDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadNewActors(form.start_page)
    return CommonResponse()


@router.post("/group", response_model=CommonResponse)
def download_by_group(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadByActorGroup(form.actor_group_id)
    return CommonResponse()


@router.patch("/resume/{actor_id}", response_model=CommonResponse)
def resume_actor(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.resumeVideoLimit())
    task = NewTask()
    task.setLimit(limit)
    task.resumeActor(actor_id)
    return CommonResponse()


@router.patch("/fix_posts/{actor_id}", response_model=CommonResponse)
def fix_posts(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.fixPostsLimit())
    task = NewTask()
    task.setLimit(limit)
    task.fix_posts_of_actor(actor_id)
    return CommonResponse()


@router.post("/manual", response_model=CommonResponse)
def manual(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.manual()
    return CommonResponse()


def _add_task(actor_id: int, download_limit: DownloadLimitForm):
    limit = DownloadLimit(download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.downloadSpecificActor(actor_id)


@router.post("/specific", response_model=CommonResponse)
def download_specific(form: ActorIdDownloadForm):
    for actor_id in form.actor_ids:
        x = threading.Thread(target=_add_task, args=(
            actor_id, form.download_limit,))
        x.start()
    return CommonResponse()


@router.post("/urls", response_model=CommonResponse)
def download_by_urls(form: UrlDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    task.downloadByUrls(form.urls)
    return CommonResponse()


@router.get("/count", response_model=UnifiedResponse[int])
def get_task_count():
    return UnifiedResponse[int](data=GetTaskCount())


@router.get("/list", response_model=UnifiedListResponse[DownloadTaskResponse])
def get_tasks():
    tasks = [task.toResponse() for task in GetAllTask()]
    return UnifiedListResponse[DownloadTaskResponse](data=tasks)


@router.get("/actor_ids", response_model=UnifiedListResponse[int])
def get_task_actor_ids():
    return UnifiedListResponse[int](data=GetActorIds())


# must before @router.delete("/{task_uid}")
@router.delete("/all", response_model=CommonResponse)
def stop_all_task():
    StopAllTasks()
    return CommonResponse()


@router.delete("/{task_uid}", response_model=CommonResponse)
def stop_task(task_uid: int):
    StopTask(task_uid)
    return CommonResponse()


@router.get("/clean", response_model=CommonResponse)
def clean_files(session: Session = Depends(DbCtrl.get_db_session)):
    ActorFileCtrl.removeOutdatedFiles(session)
    return CommonResponse()


@router.get("/logs", response_model=CommonResponse)
def open_log_folder():
    cur_dir = os.getcwd()
    subprocess.Popen(f'explorer {cur_dir}\\logs')
    return CommonResponse()
