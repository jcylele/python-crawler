import asyncio
import re
from sqlalchemy import func
from sqlalchemy.orm import Session
from playwright.async_api import Page, Response, expect, TimeoutError as PlaywrightTimeoutError

import Configs
from Consts import WorkerType, NoticeType, ActorLogType
from Ctrls import ActorCtrl, CommonCtrl, DbCtrl, RequestCtrl, PostCtrl, NoticeCtrl, ActorLogCtrl
from Models.ModelInfos import ActorInfo, PostInfo
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem
from Workers.ImageWait.ActorIconWait import ActorIconWait
from Workers.BaseFetchWorker import BaseFetchWorker
from Workers.ImageWait.ThumbnailWait import ActorThumbnailWait

# max number of post id
MAX_POST_ID = 1 << 64 - 1


class FetchActorWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.FetchActor, task=task)
        self.actor_info: ActorInfo | None = None
        self.actor_icon_wait = ActorIconWait()
        self.actor_thumbnail_wait = ActorThumbnailWait()
        self.actor_thumbnail_wait.set_wait(task.wait_thumbnail)

    async def processPosts(self, post_list: list[PostInfo], from_url: str) -> bool:
        reach_last = False
        posts_to_enqueue: list[PostInfo] = []
        with DbCtrl.getSession() as session, session.begin():
            actor_id = self.actor_info.actor_id
            actor = CommonCtrl.getActor(session, actor_id)
            last_post_id = 0 if self.task.is_all_posts() else actor.last_post_id
            for post_info in post_list:
                if post_info.post_id <= last_post_id:
                    reach_last = True
                    continue
                post = CommonCtrl.tryGetPost(session, post_info.post_id)
                if post is None:
                    PostCtrl.addPost(session, self.actor_info, post_info)
                    posts_to_enqueue.append(post_info)
                else:
                    if post.actor_id != actor_id:
                        owner_actor = CommonCtrl.getActor(
                            session, post.actor_id)
                        ActorCtrl.fixPostBelong(
                            session, post, owner_actor, actor)
                        if self.task.is_fix_posts:
                            await self.task.fix_more_posts(owner_actor.actor_id)

                    elif not post.completed:  # the post is not analysed yet
                        posts_to_enqueue.append(post_info)
                    else:  # all resources of the post are already added
                        await self.queue_mgr().enqueueAllRes(
                            self.actor_info, post, self.DownloadLimit())
                    # update scan version
                    post.scan_version = self.actor_info.post_scan_version

        # 在事务提交后，再将所有任务推入队列
        for post_info in posts_to_enqueue:
            await self.queue_mgr().enqueueFetchPost(self.actor_info, post_info)

        return reach_last

    def updateActorPostScanVersion(self):
        with DbCtrl.getSession() as session, session.begin():
            new_version = self.actor_info.post_scan_version
            actor = CommonCtrl.getActor(session, self.actor_info.actor_id)
            actor.post_scan_version = new_version
            actor.has_missing_posts = PostCtrl.hasMissingPosts(
                session, self.actor_info.actor_id, new_version)

    @staticmethod
    def updateActorPostCount(actor_id: int, post_count: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = CommonCtrl.getActor(session, actor_id)
            if actor.total_post_count != post_count:
                actor.total_post_count = post_count
                ActorLogCtrl.addActorLog(
                    session, actor_id, ActorLogType.PostCount, post_count)
            actor.update_last_fetch_time()

    @staticmethod
    def addInvalidPostNotice(actor_name: str, post_id_str: str):
        with DbCtrl.getSession() as session, session.begin():
            NoticeCtrl.addNotice(
                session, NoticeType.InvalidPost, actor_name, post_id_str)

    def _loadSelector(self) -> str:
        return ".user-header"

    def _url(self, item: FetchActorQueueItem) -> str:
        return RequestCtrl.formatActorUrl(self.actor_info)

    def _checkFetch(self, session: Session, item: FetchActorQueueItem):
        # return self.hasActorFolder(session, item.actor_id)
        return True

    def _beforeFetch(self, session: Session, item: FetchActorQueueItem):
        self.actor_info = self.getActorInfo(item.actor_id)
        if self.task.is_fix_posts:
            self.actor_info.post_scan_version += 1

        self.actor_icon_wait.set_actor_info(self.actor_info)

        if self.actor_thumbnail_wait.get_wait():
            self.actor_thumbnail_wait.set_folder_path(
                Configs.formatActorThumbnailFolderPath(
                    self.actor_info.actor_id, self.actor_info.actor_name
                ))

    async def _setup_page(self, page: Page):
        if not self.actor_thumbnail_wait.get_wait():
            await page.route("**/*", self._thumbnail_block_handler)

    async def on_response(self, response: Response):
        await self.actor_icon_wait.on_response(response)
        await self.actor_thumbnail_wait.on_response(response)

    async def _onFetched(self, item: FetchActorQueueItem, page: Page) -> bool:
        actor_name = self.actor_info.actor_name

        # actor icon
        await self.actor_icon_wait.wait(page)

        # update post count
        post_count = 0
        post_count_updated = False
        page_finished = False

        # Loop through pages, using i as the expected page number
        for i in range(1, 1000000):
            LogUtil.info(f"actor {actor_name} page {i}")

            top_paginator = page.locator("#paginator-top")

            # Try to update total post count from paginator if it exists and hasn't been updated yet
            if (await top_paginator.count()) > 0 and not post_count_updated:
                try:
                    ele_count_text = await top_paginator.locator('small').text_content(timeout=5000)
                    if ele_count_text:
                        nums = re.findall(r"\d+", ele_count_text)
                        if nums:
                            FetchActorWorker.updateActorPostCount(
                                item.actor_id, int(nums[-1]))
                            post_count_updated = True
                except PlaywrightTimeoutError:
                    LogUtil.info(
                        f"actor {actor_name} post count not found, assuming a single page.")

            top_menu = top_paginator.locator('menu')

            # If a page menu exists, wait for the current page number to be correct
            if (await top_menu.count()) > 0:
                try:
                    await expect(top_menu.locator(".pagination-button-current b")).to_have_text(f"{i}", timeout=10000)
                except PlaywrightTimeoutError:
                    LogUtil.error(
                        f"actor {actor_name} page {i} not found or timed out")
                    break
            else:
                if i > 1:
                    # If we are past the first page and the menu disappears, we are done.
                    LogUtil.warning(
                        f"Paginator not found on page {i} for actor {actor_name}, ending.")
                    break
                LogUtil.info(
                    f"actor {actor_name} has no page menu, assuming a single page.")

            # Analyze content
            article_locators = await page.locator('article.post-card').all()
            post_list: list[PostInfo] = []
            for article_locator in article_locators:
                post_id_str = await article_locator.get_attribute("data-id")
                if post_id_str is None:
                    continue
                post_id = PostInfo.parsePostId(post_id_str)
                if post_id == 0:
                    FetchActorWorker.addInvalidPostNotice(
                        actor_name, post_id_str)
                    LogUtil.error(
                        f"actor {actor_name} page {i} post {post_id_str} invalid")
                    continue
                thumbnail_locator = article_locator.locator(
                    ".post-card__image-container")
                has_thumbnail = (await thumbnail_locator.count()) > 0
                post_list.append(PostInfo(post_id, post_id_str, has_thumbnail))

            reach_last_post = await self.processPosts(post_list, page.url)
            post_count += len(post_list)

            await self.actor_thumbnail_wait.wait(page)

            # If post count was never updated from a paginator, it's a single page.
            # Update the count with the number of posts found on this page.
            if not post_count_updated:
                FetchActorWorker.updateActorPostCount(
                    item.actor_id, len(post_list))
                post_count_updated = True

            # Check break conditions
            if reach_last_post or (not self.DownloadLimit().morePost(post_count)):
                break

            # Next page logic
            # If there's no page menu, it's the last page.
            if (await top_menu.count()) == 0:
                page_finished = True
                break

            next_btn_locator = top_menu.locator(
                '.pagination-button-after-current')
            # If there's no 'next' button, it's the last page.
            if (await next_btn_locator.count()) == 0:
                page_finished = True
                break

            # If the 'next' button is disabled, it's the last page.
            next_btn_classes = await next_btn_locator.get_attribute("class")
            if next_btn_classes and "pagination-button-disabled" in next_btn_classes:
                page_finished = True
                break

            # slow down to avoid being blocked
            await asyncio.sleep(2)
            # Click to go to the next page
            await next_btn_locator.click()

        if self.task.is_fix_posts and page_finished:
            self.updateActorPostScanVersion()

        return True
