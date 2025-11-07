
import os
import subprocess
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Ctrls import ActorFileCtrl, ActorSimilarCtrl, DbCtrl, ManualCtrl, ResFileCtrl
from Utils import CacheUtil
from routers.schemas_others import CommonResponse, SettingItem, Settings, UnifiedResponse


router = APIRouter(
    prefix="/api/others",
    tags=["others"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/reset_manual", response_model=CommonResponse)
def reset_manual(session: Session = Depends(DbCtrl.get_db_session)):
    ManualCtrl.resetManual(session)
    return CommonResponse()


@router.get("/similar_names", response_model=CommonResponse)
def similar_names(session: Session = Depends(DbCtrl.get_db_session)):
    ActorSimilarCtrl.check_similar_names(session)
    return CommonResponse()


@router.get("/remove_outdated", response_model=CommonResponse)
def remove_outdated_files(session: Session = Depends(DbCtrl.get_db_session)):
    ResFileCtrl.removeOutdatedFiles(session)
    return CommonResponse()


@router.get("/logs", response_model=CommonResponse)
def open_log_folder():
    cur_dir = os.getcwd()
    subprocess.Popen(f'explorer {cur_dir}\\logs')
    return CommonResponse()


@router.get("/custom_page", response_model=UnifiedResponse[int])
def get_custom_page():
    page = CacheUtil.getCustomPage()
    return UnifiedResponse[int](data=page)


@router.get("/settings", response_model=UnifiedResponse[Settings])
def get_settings():
    settings = CacheUtil.getSettings()
    return UnifiedResponse[Settings](data=settings)


@router.post("/change_setting", response_model=CommonResponse)
def change_setting(setting_item: SettingItem):
    CacheUtil.changeSetting(setting_item.key, setting_item.value)
    return CommonResponse()
