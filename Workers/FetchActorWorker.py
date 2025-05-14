import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Consts import WorkerType, QueueType, NoticeType, ActorLogType
from Ctrls import ActorCtrl, DbCtrl, RequestCtrl, PostCtrl, NoticeCtrl, ActorLogCtrl
from Download import QueueUtil
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker

# max number of post id
MAX_POST_ID = 1 << 64 - 1


class FetchActorWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchActor, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchActor

    def processPosts(self, post_list: list[(int, bool)], from_url: str) -> bool:
        # print("processPosts " +",".join([str(i) for i in post_list]))
        with DbCtrl.getSession() as session, session.begin():
            actor_id = self.actor_info.actor_id
            actor = ActorCtrl.getActor(session, actor_id)
            last_post_id = actor.last_post_id
            reach_last = False
            for tup_post in post_list:
                (post_id, is_dm) = tup_post
                if post_id <= last_post_id:
                    reach_last = True
                    continue
                post = PostCtrl.getPost(session, post_id)
                if post is None:
                    PostCtrl.addPost(session, actor_id, post_id, is_dm)
                    # QueueUtil.enqueuePost(self.QueueMgr(), self.actor_info, post_id, is_dm, from_url)
                    QueueUtil.enqueueFetchPost(self.QueueMgr(), self.actor_info, post_id, is_dm)
                else:
                    if post.actor_id != actor_id:
                        owner_actor = post.actor
                        if actor.main_actor_id != owner_actor.main_actor_id or actor.main_actor_id == 0:
                            NoticeCtrl.addNoticeStrict(session, NoticeType.UnlinkedActor,
                                                       [actor.actor_name, owner_actor.actor_name])
                            LogUtil.error(
                                f"same post {post.post_id} for {post.actor.actor_name} and {actor.actor_name}")
                    elif not post.completed:  # the post is not analysed yet
                        # QueueUtil.enqueuePost(self.QueueMgr(), self.actor_info, post_id, is_dm, from_url)
                        QueueUtil.enqueueFetchPost(self.QueueMgr(), self.actor_info, post_id, is_dm)
                    else:  # all resources of the post are already added
                        QueueUtil.enqueueAllRes(self.QueueMgr(), self.actor_info, post, self.DownloadLimit())
            return reach_last

    @staticmethod
    def updateActorPostCount(actor_id: int, post_count: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_id)
            if actor.total_post_count != post_count:
                actor.total_post_count = post_count
                ActorLogCtrl.addActorLog(session, actor_id, ActorLogType.PostCount, post_count)

    @staticmethod
    def addInvalidPostNotice(actor_name: str, page: int, post_id_str: str):
        with DbCtrl.getSession() as session, session.begin():
            NoticeCtrl.addNotice(session, NoticeType.InvalidPost, actor_name, str(page), post_id_str)

    @staticmethod
    def elementInClass(element: WebElement, class_name: str):
        return element.get_attribute("class").find(class_name) != -1

    def _loadSelector(self) -> str:
        return ".user-header"

    def _url(self, item: FetchActorQueueItem) -> str:
        actor_info = self.getActorInfo(item.actor_id)
        return RequestCtrl.formatActorUrl(actor_info)

    def _checkFetch(self, item: FetchActorQueueItem):
        return self.hasActorFolder(item.actor_id)

    def _onFetched(self, item: FetchActorQueueItem, driver: webdriver.Chrome) -> bool:
        self.actor_info = self.getActorInfo(item.actor_id)
        actor_name = self.actor_info.actor_name

        # create folder
        ActorCtrl.createActorFolder(self.actor_info)

        # actor icon
        self._saveActorIcon(self.actor_info, ".user-header__avatar img", driver, True)

        # update post count
        post_count = 0
        post_count_updated = False

        # webpage is new in every iteration, so keep elements inside the loop
        for i in range(1, 1000000):
            try:
                paginator_top = driver.find_element(By.CSS_SELECTOR, "#paginator-top")
            except:
                paginator_top = None

            if paginator_top is not None and not post_count_updated:
                try:
                    ele_count = paginator_top.find_element(By.CSS_SELECTOR, 'small')
                    nums = re.findall(r"\d+", ele_count.text)
                    FetchActorWorker.updateActorPostCount(item.actor_id, int(nums[-1]))
                    post_count_updated = True
                except:
                    pass

            try:
                page_menu = paginator_top.find_element(By.CSS_SELECTOR, 'menu')
            except:
                page_menu = None

            LogUtil.info(f"actor {actor_name} page {i}")
            # wait for page load
            if page_menu is not None:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".pagination-button-current b"), f"{i}")
                    )
                except:
                    LogUtil.error(f"actor {actor_name} page {i} not found")
                    break
            else:
                LogUtil.info(f"actor {actor_name} page {i} no page menu")

            # analyze content
            article_list = driver.find_elements(By.CSS_SELECTOR, 'article.post-card')
            post_list = []
            for article in article_list:
                post_id_str = article.get_attribute("data-id")
                if post_id_str is None:
                    continue
                is_dm = post_id_str.startswith('DM')
                try:
                    if is_dm:
                        post_id = int(post_id_str[2:])
                    else:
                        post_id = int(post_id_str)
                    if post_id > MAX_POST_ID:
                        raise ValueError
                except:
                    FetchActorWorker.addInvalidPostNotice(actor_name, i, post_id_str)
                    LogUtil.error(f"actor {actor_name} page {i} post {post_id_str} invalid")
                    continue
                post_list.append((post_id, is_dm))
            reach_last_post = self.processPosts(post_list, driver.current_url)
            post_count += len(post_list)

            # only one page
            if not post_count_updated:
                FetchActorWorker.updateActorPostCount(item.actor_id, len(post_list))
                post_count_updated = True

            # download no more
            if reach_last_post or (not self.DownloadLimit().morePost(post_count)):
                break

            # next page
            next_btn = None
            if page_menu is not None:
                try:
                    next_btn = page_menu.find_element(By.CSS_SELECTOR, '.pagination-button-after-current')

                except:
                    pass

            if next_btn is None or FetchActorWorker.elementInClass(next_btn, "pagination-button-disabled"):
                break

            # click
            next_btn.click()
            # wait
            time.sleep(3)

        return True
