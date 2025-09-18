import os
import re
from playwright.async_api import Page, Locator, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

import Configs
from Consts import WorkerType, ResType
from Ctrls import DbCtrl, RequestCtrl, PostCtrl, ResCtrl
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchPostQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker
from Workers.ImageWait.PostThumbnailWait import PostThumbnailWait


class FetchPostWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.FetchPost, task=task)
        self.thumbnail_wait = PostThumbnailWait()
        self.thumbnail_wait.set_wait(task.download_limit.allowResDownload(
            ResType.Image))

    async def _getResUrl(self, res_node: Locator):
        a_node = res_node.locator("a")
        if (await a_node.count()) == 0:
            return None
        href = await a_node.get_attribute("href")
        # error defence
        if href.endswith("f=undefined"):
            # LogUtil.warn(f"{item} undefined res")
            return None

        return RequestCtrl.formatFullUrl(href)

    def _loadSelector(self) -> str:
        return ".post__body"

    def _url(self, item: FetchPostQueueItem) -> str:
        return RequestCtrl.formatPostUrl(item.actor_info, item.post_id, item.is_dm)

    def _checkFetch(self, session: Session, item: FetchPostQueueItem):
        # check actor folder
        if not self.hasActorFolder(session, item.actor_info.actor_id):
            return False
        # check post completed, no need to fetch
        post = PostCtrl.getPost(session, item.post_id)
        if post is None:  # queue push before sql commit?
            LogUtil.error(
                f"post {item.post_id} of actor {item.actor_info.actor_name} not found")
            return False
        if post.completed:
            return False
        # check res exists, no need to fetch
        res = ResCtrl.getResByIndex(session, item.post_id, 1)
        if res is not None:
            LogUtil.error(
                f"post {item.post_id} of actor {item.actor_info.actor_name} already fetched, but not completed")
            return False

        return True

    def _beforeFetch(self, session: Session, item: FetchPostQueueItem):
        if self.thumbnail_wait.get_wait():
            self.thumbnail_wait.set_folder_path(
                Configs.formatActorThumbnailFolderPath(
                    item.actor_info.actor_id, item.actor_info.actor_name
                ))

    async def on_response(self, response: Response):
        await self.thumbnail_wait.on_response(response)

    async def _onFetched(self, item: FetchPostQueueItem, page: Page) -> bool:

        # analyze res
        url_list = []

        image_list = await page.locator('.post__thumbnail').all()
        for image_node in image_list:
            url = await self._getResUrl(image_node)
            if url is not None:
                url_list.append((ResType.Image, url))

        video_list = await page.locator('.post__attachment').all()
        for video_node in video_list:
            url = await self._getResUrl(video_node)
            if url is not None:
                url_list.append((ResType.Video, url))

        # write to db, enqueue items
        with DbCtrl.getSession() as session, session.begin():
            post = PostCtrl.getPost(session, item.post_id)

            if len(url_list) > 0:
                # add records for the resources
                ResCtrl.addAllRes(session, item.post_id, url_list)
                # enqueue all resources of the post
                await self.queue_mgr().enqueueAllRes(item.actor_info, post, self.DownloadLimit())

            # mark the post as analysed
            post.completed = True

        await self.thumbnail_wait.wait(page)

        return True
