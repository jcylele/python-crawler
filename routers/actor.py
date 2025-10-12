import subprocess
from typing import TypeAlias

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.params import Query, Body

import Configs
from Consts import ErrorCode
from Ctrls import ActorFileCtrl, ActorLinkCtrl, ActorQueryCtrl, ActorSimilarCtrl, DbCtrl, ActorCtrl, ActorLogCtrl, ResCtrl, ManualCtrl, ResFileCtrl
from routers.schemas import ActorFileInfoResponse, ActorLogResponse, ActorResponse
from routers.schemas_others import ActorAbstract, ActorVideoInfo, CommentCount, CommonResponse, ResFileInfo, ActorFileDetail, ResSizeCount, UnifiedListResponse, UnifiedResponse
from routers.web_data import ActorConditionForm, BatchActorGroup, LinkActorForm

router = APIRouter(
    prefix="/api/actor",
    tags=["actor"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

ActorResult: TypeAlias = UnifiedResponse[ActorResponse]
ActorListResult: TypeAlias = UnifiedResponse[list[ActorResponse]]


@router.post("/count", response_model=UnifiedResponse[int])
def get_actor_count(form: ActorConditionForm, session: Session = Depends(DbCtrl.get_db_session)):
    actor_count = ActorQueryCtrl.getActorCount(session, form)
    return UnifiedResponse[int](data=actor_count)


@router.get("/group_count", response_model=UnifiedResponse[dict[int, int]])
def get_actor_count_of_groups(session: Session = Depends(DbCtrl.get_db_session)):
    group_count = ActorQueryCtrl.getActorCountInGroups(session)
    return UnifiedResponse[dict[int, int]](data=group_count)


@router.post("/list", response_model=UnifiedResponse[list[int]])
def get_actor_list(*, form: ActorConditionForm, limit: int, start: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_list = ActorQueryCtrl.getActorList(session, form, limit, start)
    return UnifiedResponse[list[int]](data=actor_list)


@router.post("/link", response_model=ActorListResult)
def link_actors(form: LinkActorForm, session: Session = Depends(DbCtrl.get_db_session)):
    # complex logic, ensure transaction is done
    error_code = ActorLinkCtrl.linkActors(session, form)

    if error_code != ErrorCode.Success:
        return ActorListResult(error_code=error_code)

    actors = [ActorCtrl.getActor(session, actor_id)
              for actor_id in form.actor_ids]
    return ActorListResult(data=actors)


@router.post("/unlink", response_model=ActorListResult)
def unlink_actors(actor_ids: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    error_code = ActorLinkCtrl.unlinkActors(session, actor_ids)

    if error_code != ErrorCode.Success:
        return ActorListResult(error_code=error_code)

    actors = [ActorCtrl.getActor(session, actor_id)
              for actor_id in actor_ids]
    return ActorListResult(data=actors)


@router.post("/batch/group", response_model=UnifiedResponse[list[ActorResult]])
def batch_set_group(form: BatchActorGroup, session: Session = Depends(DbCtrl.get_db_session)):
    ar_list = []
    for actor_id in form.actor_ids:
        error_code, actor = ActorCtrl.changeActorGroup(
            session, actor_id, form.group_id)
        ar_list.append(ActorResult(error_code=error_code, data=actor))
    return UnifiedResponse[list[ActorResult]](data=ar_list)


@router.get("/clear_group_folder/{group_id}", response_model=CommonResponse)
def clear_folder_by_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actors = ActorQueryCtrl.getActorsByGroup(session, group_id)
    for actor in actors:
        ActorFileCtrl.clearActorFolder(session, actor)
    return CommonResponse()


@router.get("/validate_all_file_info", response_model=UnifiedResponse[int])
def validate_all_file_info(session: Session = Depends(DbCtrl.get_db_session)):
    return CommonResponse(error_code=ErrorCode.Unavailable)


@router.get("/comments", response_model=UnifiedListResponse[CommentCount])
def get_comments(session: Session = Depends(DbCtrl.get_db_session)):
    comments = ActorQueryCtrl.getComments(session)
    return UnifiedListResponse[CommentCount](data=comments)

# 同方法(get)按顺序匹配, 固定前缀在前，{actor_id}在后, 以下皆为单个匹配


@router.get("/{actor_id}", response_model=ActorResult)
def get_actor(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    if actor is None:
        return ActorResult(error_code=ErrorCode.ActorNotFound)
    return ActorResult(data=actor)


@router.get("/{actor_id}/abstract", response_model=UnifiedResponse[ActorAbstract])
def get_actor_abstract(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_abstract = ActorCtrl.getActorAbstract(session, actor_id)
    if actor_abstract is None:
        return UnifiedResponse[ActorAbstract](error_code=ErrorCode.ActorNotFound)
    return UnifiedResponse[ActorAbstract](data=actor_abstract)


@router.patch("/{actor_id}/group", response_model=ActorResult)
def change_actor_group(actor_id: int, actor_group_id: int = Query(alias='val'), session: Session = Depends(DbCtrl.get_db_session)):
    error_code, actor = ActorCtrl.changeActorGroup(
        session, actor_id, actor_group_id)
    return ActorResult(error_code=error_code, data=actor)


@router.patch("/{actor_id}/score", response_model=ActorListResult)
def change_actor_score(actor_id: int, score: int = Query(alias='val'), session: Session = Depends(DbCtrl.get_db_session)):
    actors = ActorCtrl.changeActorScore(session, actor_id, score)
    return ActorListResult(data=actors)


@router.post("/{actor_id}/remark", response_model=ActorListResult)
def set_actor_remark(actor_id: int, remark: str = Body(default="", media_type="text/plain"), session: Session = Depends(DbCtrl.get_db_session)):
    actors = ActorCtrl.changeActorRemark(session, actor_id, remark)
    return ActorListResult(data=actors)


@router.post("/{actor_id}/comment", response_model=ActorResult)
def set_actor_comment(actor_id: int, comment: str = Body(default="", media_type="text/plain"), session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.changeActorComment(session, actor_id, comment)
    return ActorResult(data=actor)


@router.post("/{actor_id}/tag", response_model=ActorListResult)
def change_actor_tag(actor_id: int, tag_list: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    actors = ActorCtrl.changeActorTags(session, actor_id, tag_list)
    return ActorListResult(data=actors)


@router.get("/{actor_id}/open", response_model=CommonResponse)
def open_actor_folder(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    ResFileCtrl.remove_thumbnail_images(session, actor)
    subprocess.Popen(
        f'explorer "{Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)}"')
    return CommonResponse()


@router.patch("/{actor_id}/reset_posts", response_model=UnifiedResponse[ActorFileDetail])
def reset_actor_posts(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorCtrl.resetActorPosts(session, actor_id)
    session.flush()
    actor_file_detail = ActorFileCtrl.getActorFileDetail(session, actor_id)
    return UnifiedResponse[ActorFileDetail](data=actor_file_detail)


@router.patch("/{actor_id}/clear", response_model=UnifiedResponse[ActorFileDetail])
def clear_actor_folder(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    ActorFileCtrl.clearActorFolder(session, actor)
    session.flush()
    actor_file_detail = ActorFileCtrl.getActorFileDetail(session, actor_id)
    return UnifiedResponse[ActorFileDetail](data=actor_file_detail)


@router.get("/{actor_id}/file_info", response_model=UnifiedResponse[ActorFileDetail])
def get_actor_file_info(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_file_detail = ActorFileCtrl.getActorFileDetail(session, actor_id)
    return UnifiedResponse[ActorFileDetail](data=actor_file_detail)


@router.patch("/{actor_id}/validate_file_info", response_model=UnifiedListResponse[ActorFileInfoResponse])
def validate_actor_file_info(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_file_info_list = ActorFileCtrl.validateActorFileInfo(
        session, actor_id)
    return UnifiedListResponse[ActorFileInfoResponse](data=actor_file_info_list)


@router.get("/{actor_id}/video_stats", response_model=UnifiedListResponse[ActorVideoInfo])
def get_actor_video_stats(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_video_stats = ActorFileCtrl.getActorVideoStats(session, actor_id)
    return UnifiedListResponse[ActorVideoInfo](data=actor_video_stats)


@router.get("/{actor_id}/downloading_files", response_model=UnifiedListResponse[ResFileInfo])
def get_downloading_files(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    downloading_files = ResFileCtrl.getDownloadingFilesOfActor(session, actor)
    return UnifiedListResponse[ResFileInfo](data=downloading_files)


@router.delete("/{actor_id}/remove_downloading_files", response_model=CommonResponse)
def remove_downloading_files(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    ResFileCtrl.removeDownloadingFilesOfActor(session, actor)
    return CommonResponse()


@router.get("/{actor_id}/rename_files", response_model=CommonResponse)
def rename_actor_files(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    ResFileCtrl.rename_actor_files(session, actor)
    return CommonResponse()


@router.get("/{actor_id}/linked", response_model=UnifiedResponse[list[int]])
def get_linked_actors(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.getActor(session, actor_id)
    if not actor.is_linked:
        return UnifiedResponse[list[int]](data=[actor_id])
    linked_actor_ids = ActorCtrl.getLinkedActorIds(
        session, actor.main_actor_id)
    return UnifiedResponse[list[int]](data=linked_actor_ids)


@router.get("/{actor_id}/linked_groups", response_model=UnifiedResponse[list[int]])
def get_linked_groups(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    group_ids = ActorLinkCtrl.getGroupsOfLinkedActors(session, actor_id)
    return UnifiedResponse[list[int]](data=group_ids)


@router.get("/{actor_id}/logs", response_model=UnifiedListResponse[ActorLogResponse])
def get_logs(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_logs = ActorLogCtrl.getActorLogs(session, actor_id)
    return UnifiedListResponse[ActorLogResponse](data=actor_logs)


@router.get("/{actor_id}/video_sizes", response_model=UnifiedListResponse[ResSizeCount])
def get_video_sizes(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    video_sizes = ResCtrl.getResSizesOfActor(session, actor_id)
    return UnifiedListResponse[ResSizeCount](data=video_sizes)
