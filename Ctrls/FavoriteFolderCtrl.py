from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from routers.web_data import FavoriteFolderForm
from Models.FavoriteFolderModel import FavoriteFolderModel
from Models.ActorFavoriteRelationship import ActorFavoriteRelationship
from Models.ActorModel import ActorModel


def createFolder(session: Session, form: FavoriteFolderForm) -> FavoriteFolderModel:
    ff = FavoriteFolderModel(
        folder_name=form.folder_name,
        folder_desc=form.folder_desc
    )
    session.add(ff)
    session.flush()
    return ff


def getFolder(session: Session, folder_id: int) -> FavoriteFolderModel:
    return session.get(FavoriteFolderModel, folder_id)


def updateFolder(session: Session, folder_id: int, form: FavoriteFolderForm) -> FavoriteFolderModel:
    ff = session.get(FavoriteFolderModel, folder_id)
    ff.folder_name = form.folder_name
    ff.folder_desc = form.folder_desc
    session.flush()
    return ff


def getFolders(session: Session) -> list[FavoriteFolderModel]:
    stmt = select(FavoriteFolderModel).order_by(FavoriteFolderModel.folder_id)
    return list(session.scalars(stmt))


def deleteFolder(session: Session, folder_id: int):
    stmt = delete(FavoriteFolderModel).where(
        FavoriteFolderModel.folder_id == folder_id
    )
    session.execute(stmt)
    session.flush()


def getActorsInFolder(session: Session, folder_id: int):
    stmt = select(ActorModel).join(
        ActorFavoriteRelationship,
        ActorModel.actor_id == ActorFavoriteRelationship.actor_id
    ).where(
        ActorFavoriteRelationship.folder_id == folder_id
    ).order_by(
        ActorFavoriteRelationship.folder_order
    )
    return list(session.scalars(stmt))


def getMaxOrder(session: Session, folder_id: int) -> int:
    return session.query(func.max(ActorFavoriteRelationship.folder_order)).filter(
        ActorFavoriteRelationship.folder_id == folder_id
    ).scalar() or 0


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

    # get max order
    max_order = getMaxOrder(session, folder_id)

    max_order += 1

    alr = ActorFavoriteRelationship(
        folder_id=folder_id,
        actor_id=actor_id,
        folder_order=max_order
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

    # get max order
    max_order = getMaxOrder(session, folder_id)

    for actor_id in actor_id_set:
        max_order += 1
        alr = ActorFavoriteRelationship(
            folder_id=folder_id,
            actor_id=actor_id,
            folder_order=max_order
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


def reorderActors(session: Session, folder_id: int, actor_ids: list[int]):
    # delete all existing relationships
    stmt = delete(ActorFavoriteRelationship).where(
        ActorFavoriteRelationship.folder_id == folder_id
    )
    session.execute(stmt)
    session.flush()

    # add new relationships
    for i, actor_id in enumerate(actor_ids):
        alr = ActorFavoriteRelationship(
            folder_id=folder_id,
            actor_id=actor_id,
            folder_order=i+1
        )
        session.add(alr)
    session.flush()
