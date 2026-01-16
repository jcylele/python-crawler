from typing import TypeAlias
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Consts import ErrorCode
from Ctrls import FavoriteFolderCtrl, DbCtrl
from routers.web_data import CommonGroupForm, CommonPriority
from routers.schemas_others import CommonResponse, UnifiedListResponse, UnifiedResponse
from routers.schemas import FavoriteFolderResponse

router = APIRouter(
    prefix="/api/favorite_folder",
    tags=["favorite_folder"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

FavoriteFolderResult: TypeAlias = UnifiedResponse[FavoriteFolderResponse]


@router.get("/list", response_model=UnifiedListResponse[FavoriteFolderResponse])
def get_folder_list(session: Session = Depends(DbCtrl.get_db_session)):
    folders = FavoriteFolderCtrl.getFolders(session)
    return UnifiedListResponse[FavoriteFolderResponse](data=folders)


@router.post("/add", response_model=FavoriteFolderResult)
def add_folder(form: CommonGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    folder = FavoriteFolderCtrl.createFolder(session, form)
    return FavoriteFolderResult(data=folder)


@router.post("/priority", response_model=CommonResponse)
def update_priorities(priority_list: list[CommonPriority], session: Session = Depends(DbCtrl.get_db_session)):
    for p in priority_list:
        ff = FavoriteFolderCtrl.getFolder(session, p.id)
        ff.folder_priority = p.priority
    return CommonResponse()


@router.post("/{folder_id}/update", response_model=FavoriteFolderResult)
def update_folder(folder_id: int, form: CommonGroupForm, session: Session = Depends(DbCtrl.get_db_session)):
    folder = FavoriteFolderCtrl.updateFolder(session, folder_id, form)
    return FavoriteFolderResult(data=folder)


@router.delete("/{folder_id}", response_model=CommonResponse)
def delete_folder(folder_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    FavoriteFolderCtrl.deleteFolder(session, folder_id)
    return CommonResponse()


@router.get("/{folder_id}", response_model=FavoriteFolderResult)
def get_folder_detail(folder_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    folder = FavoriteFolderCtrl.getFolder(session, folder_id)
    return FavoriteFolderResult(data=folder)


@router.post("/{folder_id}/add_actor/{actor_id}", response_model=CommonResponse)
def add_actor_to_folder(folder_id: int, actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    FavoriteFolderCtrl.addActorToFolder(session, folder_id, actor_id)
    return CommonResponse()


@router.post("/{folder_id}/remove_actor/{actor_id}", response_model=CommonResponse)
def remove_actor_from_folder(folder_id: int, actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    FavoriteFolderCtrl.removeActorFromFolder(session, folder_id, actor_id)
    return CommonResponse()


@router.post("/{folder_id}/batch_add_actor", response_model=CommonResponse)
def batch_add_actor_to_folder(folder_id: int, actor_ids: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    FavoriteFolderCtrl.batchAddActorToFolder(session, folder_id, actor_ids)
    return CommonResponse()


@router.post("/{folder_id}/batch_remove_actor", response_model=CommonResponse)
def batch_remove_actor_from_folder(folder_id: int, actor_ids: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    FavoriteFolderCtrl.batchRemoveActorFromFolder(
        session, folder_id, actor_ids)
    return CommonResponse()
