from fastapi import APIRouter

from Ctrls import FavoriteFolderCtrl, DbCtrl
from routers.web_data import FavoriteFolderForm


router = APIRouter(
    prefix="/api/favorite_folder",
    tags=["favorite_folder"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/list")
def get_folder_list():
    with DbCtrl.getSession() as session, session.begin():
        ff_list = FavoriteFolderCtrl.getFolders(session)
        return DbCtrl.CustomJsonResponse(ff_list)


@router.post("/add")
def add_folder(form: FavoriteFolderForm):
    with DbCtrl.getSession() as session, session.begin():
        ff = FavoriteFolderCtrl.createFolder(session, form)
        return DbCtrl.CustomJsonResponse(ff)


@router.post("/{folder_id}/update")
def update_folder(folder_id: int, form: FavoriteFolderForm):
    with DbCtrl.getSession() as session, session.begin():
        ff = FavoriteFolderCtrl.updateFolder(session, folder_id, form)
        return DbCtrl.CustomJsonResponse(ff)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.deleteFolder(session, folder_id)
        return DbCtrl.CustomJsonResponse(True)


@router.get("/{folder_id}")
def get_folder_detail(folder_id: int):
    with DbCtrl.getSession() as session, session.begin():
        ff = FavoriteFolderCtrl.getFolder(session, folder_id)
        return DbCtrl.CustomJsonResponse(ff)


@router.post("/{folder_id}/reorder")
def reorder_folder(folder_id: int, actor_ids: list[int]):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.reorderActors(session, folder_id, actor_ids)
        actors = FavoriteFolderCtrl.getActorsInFolder(session, folder_id)
        return DbCtrl.CustomJsonResponse(actors)


@router.get("/{folder_id}/actors")
def get_actors_in_folder(folder_id: int):
    with DbCtrl.getSession() as session, session.begin():
        actors = FavoriteFolderCtrl.getActorsInFolder(session, folder_id)
        return DbCtrl.CustomJsonResponse(actors)


@router.post("/{folder_id}/add_actor/{actor_id}")
def add_actor_to_folder(folder_id: int, actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.addActorToFolder(session, folder_id, actor_id)
        return DbCtrl.CustomJsonResponse(True)


@router.post("/{folder_id}/remove_actor/{actor_id}")
def remove_actor_from_folder(folder_id: int, actor_id: int):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.removeActorFromFolder(session, folder_id, actor_id)
        return DbCtrl.CustomJsonResponse(True)


@router.post("/{folder_id}/batch_add_actor")
def batch_add_actor_to_folder(folder_id: int, actor_ids: list[int]):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.batchAddActorToFolder(session, folder_id, actor_ids)
        return DbCtrl.CustomJsonResponse(True)


@router.post("/{folder_id}/batch_remove_actor")
def batch_remove_actor_from_folder(folder_id: int, actor_ids: list[int]):
    with DbCtrl.getSession() as session, session.begin():
        FavoriteFolderCtrl.batchRemoveActorFromFolder(
            session, folder_id, actor_ids)
        return DbCtrl.CustomJsonResponse(True)
