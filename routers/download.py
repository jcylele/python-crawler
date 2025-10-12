import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Ctrls import DbCtrl
from Download.DownloadLimit import DownloadLimit
from Download.TaskManager import NewTask, GetAllTask, StopTask, StopAllTasks, GetActorIds, GetTaskCount
from routers.web_data import GroupDownloadForm, ActorIdDownloadForm, UrlDownloadForm, \
    NewDownloadForm, DownloadLimitForm
from routers.schemas_others import CommonResponse, DownloadTaskResponse, UnifiedListResponse, UnifiedResponse

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/new", response_model=CommonResponse)
async def download_new_actors(form: NewDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    await task.downloadNewActors(form.start_page)
    return CommonResponse()


@router.post("/group", response_model=CommonResponse)
async def download_by_group(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    await task.downloadByActorGroup(form.actor_group_id)
    return CommonResponse()


@router.patch("/resume/{actor_id}", response_model=CommonResponse)
async def resume_actor(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.resumeVideoLimit())
    task = NewTask()
    task.setLimit(limit)
    await task.resumeActor(actor_id)
    return CommonResponse()


@router.patch("/fix_posts/{actor_id}", response_model=CommonResponse)
async def fix_posts(actor_id: int):
    limit = DownloadLimit(DownloadLimitForm.fixPostsLimit())
    task = NewTask()
    task.setLimit(limit)
    await task.fix_posts_of_actor(actor_id)
    return CommonResponse()


@router.post("/manual", response_model=CommonResponse)
async def manual(form: GroupDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    await task.manual()
    return CommonResponse()


async def _start_actor_download_task(actor_id: int, download_limit: DownloadLimitForm):
    limit = DownloadLimit(download_limit)
    task = NewTask()
    task.setLimit(limit)
    await task.downloadSpecificActor(actor_id)


@router.post("/specific", response_model=CommonResponse)
async def download_specific(form: ActorIdDownloadForm):
    for actor_id in form.actor_ids:
        asyncio.create_task(_start_actor_download_task(
            actor_id, form.download_limit))
    return CommonResponse()


@router.post("/urls", response_model=CommonResponse)
async def download_by_urls(form: UrlDownloadForm):
    limit = DownloadLimit(form.download_limit)
    task = NewTask()
    task.setLimit(limit)
    task.setInitGroup(form.actor_group_id)
    await task.downloadByUrls(form.urls)
    return CommonResponse()


@router.get("/count", response_model=UnifiedResponse[int])
def get_task_count():
    return UnifiedResponse[int](data=GetTaskCount())


@router.get("/list", response_model=UnifiedListResponse[DownloadTaskResponse])
def get_tasks(session: Session = Depends(DbCtrl.get_db_session)):
    tasks = [task.toResponse(session) for task in GetAllTask()]
    return UnifiedListResponse[DownloadTaskResponse](data=tasks)


@router.get("/actor_ids", response_model=UnifiedListResponse[int])
def get_task_actor_ids():
    return UnifiedListResponse[int](data=GetActorIds())


# must before @router.delete("/{task_uid}")
@router.delete("/all", response_model=CommonResponse)
async def stop_all_task():
    await StopAllTasks()
    return CommonResponse()


@router.delete("/{task_uid}", response_model=CommonResponse)
async def stop_task(task_uid: int):
    await StopTask(task_uid)
    return CommonResponse()



