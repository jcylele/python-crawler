from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from routers.web_data import CommonGroupForm
from Models.FavoriteFolderModel import FavoriteFolderModel
from Models.ActorFavoriteRelationship import ActorFavoriteRelationship


def __assign_form_to_folder(folder: FavoriteFolderModel, form: CommonGroupForm):
    folder.folder_name = form.name
    folder.folder_desc = form.desc
    folder.folder_priority = form.priority


def createFolder(session: Session, form: CommonGroupForm) -> FavoriteFolderModel:
    ff = FavoriteFolderModel()
    __assign_form_to_folder(ff, form)
    session.add(ff)
    session.flush()
    return ff


def getFolder(session: Session, folder_id: int) -> FavoriteFolderModel:
    return session.get(FavoriteFolderModel, folder_id)


def updateFolder(session: Session, folder_id: int, form: CommonGroupForm) -> FavoriteFolderModel:
    ff = session.get(FavoriteFolderModel, folder_id)
    __assign_form_to_folder(ff, form)
    session.flush()
    return ff


def getFolders(session: Session) -> list[FavoriteFolderModel]:
    stmt = select(FavoriteFolderModel).order_by(
        FavoriteFolderModel.folder_priority)
    return list(session.scalars(stmt))


def deleteFolder(session: Session, folder_id: int):
    stmt = delete(FavoriteFolderModel).where(
        FavoriteFolderModel.folder_id == folder_id
    )
    session.execute(stmt)
    session.flush()


def addActorToFolder(session: Session, folder_id: int, actor_id: int):
    exists = session.query(
        session.query(ActorFavoriteRelationship)
        .filter(
            ActorFavoriteRelationship.folder_id == folder_id,
            ActorFavoriteRelationship.actor_id == actor_id
        ).exists()
    ).scalar()
    if exists:
        return

    alr = ActorFavoriteRelationship(
        folder_id=folder_id,
        actor_id=actor_id
    )
    session.add(alr)
    session.flush()


def removeActorFromFolder(session: Session, folder_id: int, actor_id: int):
    stmt = delete(ActorFavoriteRelationship).where(
        ActorFavoriteRelationship.folder_id == folder_id,
        ActorFavoriteRelationship.actor_id == actor_id
    )
    session.execute(stmt)
    session.flush()


def batchAddActorToFolder(session: Session, folder_id: int, actor_ids: list[int]):
    actor_id_set = set(actor_ids)
    stmt = select(ActorFavoriteRelationship.actor_id).where(
        ActorFavoriteRelationship.folder_id == folder_id,
        ActorFavoriteRelationship.actor_id.in_(actor_id_set)
    )
    for actor_id in session.scalars(stmt):
        actor_id_set.remove(actor_id)
    if not actor_id_set:
        return

    for actor_id in actor_id_set:
        alr = ActorFavoriteRelationship(
            folder_id=folder_id,
            actor_id=actor_id
        )
        session.add(alr)

    session.flush()


def batchRemoveActorFromFolder(session: Session, folder_id: int, actor_ids: list[int]):
    stmt = delete(ActorFavoriteRelationship).where(
        ActorFavoriteRelationship.folder_id == folder_id,
        ActorFavoriteRelationship.actor_id.in_(actor_ids)
    )
    session.execute(stmt)
    session.flush()
