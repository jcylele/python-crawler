from fastapi import APIRouter

import Configs
import Entrance
from Ctrls import DbCtrl
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
    Entrance.repairRecords()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/new")
def download_new_actors(form: DownloadLimitForm):
    Configs.setConfig(form.actor_count, form.post_count, 1024 * 1024 * form.file_size)
    Entrance.initEnv()
    Entrance.downloadNewActors()
    return DbCtrl.CustomJsonResponse({'value': 'ok'})


@router.post("/category/{actor_category}")
def download_new_actors(actor_category: int, form: DownloadLimitForm):
    Configs.setConfig(form.actor_count, form.post_count, 1024 * 1024 * form.file_size)
    Entrance.initEnv()
    Entrance.downloadByActorCategory(ActorCategory(actor_category))
    return DbCtrl.CustomJsonResponse({'value': 'ok'})
