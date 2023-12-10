import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Consts import WorkerType, QueueType
from Ctrls import ActorCtrl, DbCtrl, RequestCtrl, PostCtrl
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from WorkQueue import QueueUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker


def getActorInfo(actor_name: str) -> ActorInfo:
    with DbCtrl.getSession() as session, session.begin():
        return ActorCtrl.getActorInfo(session, actor_name)


class FetchActorWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchActor, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchActor

    def processPosts(self, post_list: list[int], from_url: str):
        with DbCtrl.getSession() as session, session.begin():
            for post_id in post_list:
                post = PostCtrl.getPost(session, post_id)
                if post is None:
                    PostCtrl.addPost(session, self.actor_info.actor_name, post_id)
                    QueueUtil.enqueuePost(self.QueueMgr(), self.actor_info, post_id, from_url)
                elif not post.completed:  # the post is not analysed yet
                    QueueUtil.enqueuePost(self.QueueMgr(), self.actor_info, post_id, from_url)
                else:  # all resources of the post are already added
                    QueueUtil.enqueueAllRes(self.QueueMgr(), self.actor_info, post, self.DownloadLimit().file_size)

    @staticmethod
    def onActorCompleted(actor_name: str):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_name)
            actor.completed = True

    @staticmethod
    def updateActorPostCount(actor_name: str, post_count: int):
        with DbCtrl.getSession() as session, session.begin():
            actor = ActorCtrl.getActor(session, actor_name)
            if actor.total_post_count != post_count:
                actor.total_post_count = post_count

    def _process(self, item: FetchActorQueueItem) -> bool:
        post_count = 0
        self.actor_info = getActorInfo(item.actor_name)
        if self.actor_info is None:
            return False
        # fetch icon
        QueueUtil.enqueueActorIcon(self.QueueMgr(), self.actor_info)
        # create folder
        ActorCtrl.createActorFolder(item.actor_name)

        url = RequestCtrl.formatActorUrl(self.actor_info)
        self.driver.get(url)
        real_url = self.driver.current_url
        if not real_url.startswith(url):
            LogUtil.error(f"actor {self.actor_info.actor_name} not found")
            return True

        post_count_updated = False

        # webpage is new in every iteration, so keep elements inside the loop
        for i in range(1, 1000000):
            try:
                user_header = self.driver.find_element(By.CSS_SELECTOR, "header.user-header")
            except:
                LogUtil.info(f"failed to load {item.actor_name} page {i}, get {self.driver.title} instead")
                break

            try:
                paginator_top = self.driver.find_element(By.CSS_SELECTOR, "#paginator-top")
            except:
                paginator_top = None

            if paginator_top is not None and not post_count_updated:
                try:
                    ele_count = paginator_top.find_element(By.CSS_SELECTOR, 'small')
                    nums = re.findall(r"\d+", ele_count.text)
                    FetchActorWorker.updateActorPostCount(item.actor_name, int(nums[-1]))
                    post_count_updated = True
                except:
                    pass

            try:
                page_menu = paginator_top.find_element(By.CSS_SELECTOR, 'menu')
            except:
                page_menu = None

            LogUtil.info(f"actor {item.actor_name} page {i}")
            # wait for page load
            if page_menu is not None:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.text_to_be_present_in_element((By.CSS_SELECTOR, "li.pagination-button-current b"), f"{i}")
                    )
                except:
                    LogUtil.error(f"actor {item.actor_name} page {i} not found")
                    break
            else:
                LogUtil.info(f"actor {item.actor_name} page {i} no page menu")

            # analyze content
            article_list = self.driver.find_elements(By.CSS_SELECTOR, 'article.post-card')
            post_list = []
            for article in article_list:
                post_id = article.get_attribute("data-id")
                if post_id is None:
                    continue
                try:
                    post_id = int(post_id)
                    post_list.append(post_id)
                except:
                    LogUtil.error(f"actor {item.actor_name} page {i} post {post_id} invalid")
                    continue

            self.processPosts(post_list, real_url)
            post_count += len(post_list)

            # only one page
            if not post_count_updated:
                FetchActorWorker.updateActorPostCount(item.actor_name, len(post_list))
                post_count_updated = True

            # next page
            next_btn = None
            if page_menu is not None:
                try:
                    next_btn = page_menu.find_element(By.CSS_SELECTOR, '.next')
                except:
                    pass

            if next_btn is None:
                FetchActorWorker.onActorCompleted(item.actor_name)
                break

            # download no more
            if post_count >= self.DownloadLimit().post_count:
                break

            # js click
            self.driver.execute_script("arguments[0].click();", next_btn)
            # wait
            # driver.implicitly_wait(2)
            time.sleep(1)

        return True
