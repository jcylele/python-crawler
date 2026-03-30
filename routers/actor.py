import subprocess
from typing import TypeAlias

from fastapi import APIRouter, Depends
from fastapi.params import Body, Query
from sqlalchemy.orm import Session

import Configs
from Ctrls import (ActorCtrl, ActorFileCtrl, ActorLinkCtrl, ActorLogCtrl,
                   ActorQueryCtrl, CommonCtrl, DbCtrl, ResCtrl, ResFileCtrl,
                   WatermarkCtrl)
from Models.Exceptions import BusinessException
from routers.schemas import (ActorFileInfoResponse, ActorLogResponse,
                             ActorResponse)
from routers.schemas_others import (ActorAbstract, ActorFileDetail,
                                    ActorVideoInfo, CommentCount,
                                    CommonResponse, MissingPost,
                                    PostFetchTimeStats, ResFileInfo,
                                    ResSizeCount, UnifiedListResponse,
                                    UnifiedResponse)
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


@router.get("/actor_count_in_groups", response_model=UnifiedResponse[dict[int, int]])
def get_actor_count_of_groups(session: Session = Depends(DbCtrl.get_db_session)):
    group_count = ActorQueryCtrl.getActorCountInGroups(session)
    return UnifiedResponse[dict[int, int]](data=group_count)


@router.get("/actor_count_in_folders", response_model=UnifiedResponse[dict[int, int]])
def get_actor_count_of_folders(session: Session = Depends(DbCtrl.get_db_session)):
    folder_count = ActorQueryCtrl.getActorCountInFolders(session)
    return UnifiedResponse[dict[int, int]](data=folder_count)


@router.post("/list", response_model=UnifiedResponse[list[int]])
def get_actor_list(*, form: ActorConditionForm, limit: int, start: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_list = ActorQueryCtrl.getActorList(session, form, limit, start)
    return UnifiedResponse[list[int]](data=actor_list)


@router.post("/link", response_model=ActorListResult)
def link_actors(form: LinkActorForm, session: Session = Depends(DbCtrl.get_db_session)):
    # complex logic, ensure transaction is done
    ActorLinkCtrl.linkActors(session, form)

    actors = [CommonCtrl.getActor(session, actor_id)
              for actor_id in form.actor_ids]
    return ActorListResult(data=actors)


@router.post("/unlink", response_model=ActorListResult)
def unlink_actors(actor_ids: list[int], session: Session = Depends(DbCtrl.get_db_session)):
    ActorLinkCtrl.unlinkActors(session, actor_ids)
    actors = [CommonCtrl.getActor(session, actor_id)
              for actor_id in actor_ids]
    return ActorListResult(data=actors)


@router.post("/batch/group", response_model=UnifiedResponse[list[ActorResult]])
def batch_set_group(form: BatchActorGroup, session: Session = Depends(DbCtrl.get_db_session)):
    ar_list = []
    for actor_id in form.actor_ids:
        try:
            actor = ActorCtrl.changeActorGroup(
                session, actor_id, form.group_id)
        except BusinessException as e:
            ar_list.append(ActorResult(error_code=e.error_code))
        ar_list.append(ActorResult(data=actor))
    return UnifiedResponse[list[ActorResult]](data=ar_list)


@router.get("/clear_group_folder/{group_id}", response_model=CommonResponse)
def clear_folder_by_group(group_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actors = ActorQueryCtrl.getActorsByGroup(session, group_id)
    for actor in actors:
        ActorFileCtrl.clearActorFolder(session, actor)
    return CommonResponse()


@router.get("/comments", response_model=UnifiedListResponse[CommentCount])
def get_comments(session: Session = Depends(DbCtrl.get_db_session)):
    comments = ActorQueryCtrl.getComments(session)
    return UnifiedListResponse[CommentCount](data=comments)


@router.delete("/remove_downloading_files", response_model=CommonResponse)
def remove_downloading_files(actor_id: int = Query(default=0), percent: int = Query(default=100), session: Session = Depends(DbCtrl.get_db_session)):
    ResFileCtrl.removeDownloadingFiles(session, actor_id, percent)
    return CommonResponse()

# 同方法(get)按顺序匹配, 固定前缀在前，{actor_id}在后, 以下皆为单个匹配


@router.get("/{actor_id}", response_model=ActorResult)
def get_actor(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
    return ActorResult(data=actor)


@router.get("/{actor_id}/abstract", response_model=UnifiedResponse[ActorAbstract])
def get_actor_abstract(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor_abstract = CommonCtrl.getActorAbstract(session, actor_id)
    return UnifiedResponse[ActorAbstract](data=actor_abstract)


@router.patch("/{actor_id}/group", response_model=ActorResult)
def change_actor_group(actor_id: int, actor_group_id: int = Query(alias='val'), session: Session = Depends(DbCtrl.get_db_session)):
    actor = ActorCtrl.changeActorGroup(
        session, actor_id, actor_group_id)
    return ActorResult(data=actor)


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
    actor = CommonCtrl.getActor(session, actor_id)
    subprocess.Popen(
        f'explorer "{Configs.formatActorFolderPath(actor.actor_id, actor.actor_name)}"')
    return CommonResponse()


@router.get("/{actor_id}/open_thumbnail_folder", response_model=CommonResponse)
def open_thumbnail_folder(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
    thumbnail_folder = Configs.formatActorThumbnailFolderPath(
        actor.actor_id, actor.actor_name)
    # generate watermark
    WatermarkCtrl.extract_watermark(thumbnail_folder)
    # open folder
    subprocess.Popen(f'explorer "{thumbnail_folder}"')

    return CommonResponse()


@router.patch("/{actor_id}/reset_res_states", response_model=UnifiedResponse[ActorFileDetail])
def reset_actor_res_states(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    ActorCtrl.resetResStates(session, actor_id)
    session.flush()
    actor_file_detail = ActorFileCtrl.getActorFileDetail(session, actor_id)
    return UnifiedResponse[ActorFileDetail](data=actor_file_detail)


@router.patch("/{actor_id}/clear", response_model=UnifiedResponse[ActorFileDetail])
def clear_actor_folder(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
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
    actor = CommonCtrl.getActor(session, actor_id)
    downloading_files = ResFileCtrl.getDownloadingFilesOfActor(session, actor)
    return UnifiedListResponse[ResFileInfo](data=downloading_files)


@router.get("/{actor_id}/rename_files", response_model=CommonResponse)
def rename_actor_files(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
    ResFileCtrl.rename_actor_videos(session, actor)
    return CommonResponse()


@router.patch("/{actor_id}/remove_by_dir", response_model=CommonResponse)
def remove_by_dir(actor_id: int, is_landscape: bool = Query(default=False), session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
    ResFileCtrl.remove_by_dir(session, actor, is_landscape)
    return CommonResponse()


@router.get("/{actor_id}/linked", response_model=UnifiedResponse[list[int]])
def get_linked_actors(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
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


@router.get("/{actor_id}/post_fetch_time_stats", response_model=UnifiedListResponse[PostFetchTimeStats])
def get_post_fetch_time_stats(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    post_fetch_time_stats = ActorFileCtrl.getPostFetchTimeStats(
        session, actor_id)
    return UnifiedListResponse[PostFetchTimeStats](data=post_fetch_time_stats)


@router.get("/{actor_id}/post_fetch_dates", response_model=UnifiedListResponse[str])
def get_post_fetch_dates(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    post_fetch_dates = ActorFileCtrl.getPostFetchDates(session, actor_id)
    return UnifiedListResponse[str](data=post_fetch_dates)


@router.get("/{actor_id}/missing_posts", response_model=UnifiedListResponse[MissingPost])
def get_missing_posts(actor_id: int, session: Session = Depends(DbCtrl.get_db_session)):
    actor = CommonCtrl.getActor(session, actor_id)
    missing_posts = ResCtrl.get_missing_posts(
        session, actor_id, actor.post_scan_version)
    return UnifiedListResponse[MissingPost](data=missing_posts)


@router.post("/{actor_id}/rename", response_model=CommonResponse)
def rename_actor(actor_id: int, actor_name: str = Body(default="", media_type="text/plain"), session: Session = Depends(DbCtrl.get_db_session)):
    ActorFileCtrl.renameActor(session, actor_id, actor_name)
    return CommonResponse()
