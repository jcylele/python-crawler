import math
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from sqlalchemy.orm import Session

from Consts import CacheKey, WorkerType, QueueType
from Ctrls import ActorCtrl, DbCtrl, RequestCtrl
from Models.ActorInfo import ActorInfo
from Utils import CacheUtil, LogUtil
from Download import QueueUtil
from WorkQueue.BaseQueueItem import BaseQueueItem
from WorkQueue.FetchQueueItem import FetchActorsQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker


class FetchActorsWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchActors, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchActors

    def processActors(self, actor_infos: list[ActorInfo], cur_url: str):
        actor_ids = []
        with DbCtrl.getSession() as session, session.begin():
            for actor_info in actor_infos:
                # enqueue actor if not exists
                actor = ActorCtrl.getActorByInfo(session, actor_info)
                if actor is None and self.DownloadLimit().moreActor():
                    self.DownloadLimit().onActor()
                    actor = ActorCtrl.addActor(
                        session, actor_info, self.init_category())
                    actor_ids.append(actor.actor_id)

        for actor_id in actor_ids:
            QueueUtil.enqueueFetchActor(self.QueueMgr(), actor_id)
            QueueUtil.enqueueFetchActorLink(self.QueueMgr(), actor_id)

    def getFinishedPage(self, start_page: int) -> int:
        if start_page > 0:
            return start_page - 1
        if start_page == 0:
            return 0
        with DbCtrl.getSession() as session, session.begin():
            actor_count = ActorCtrl.getAllActorCount(session)
            return math.floor(actor_count / 50)

    def _loadSelector(self) -> str:
        return '#paginator-top menu'

    def _url(self, item: FetchActorsQueueItem) -> str:
        self.start_page = self.getFinishedPage(item.start_page) + 1
        LogUtil.info(f"fetch actors from page {self.start_page}")
        return RequestCtrl.formatActorsUrl((self.start_page - 1) * 50)

    def _checkFetch(self, session: Session, item: BaseQueueItem):
        return True

    def _onFetched(self, item: FetchActorsQueueItem, driver: webdriver.Chrome) -> bool:
        # str_next_page = ""
        while True:
            try:
                WebDriverWait(driver, 10).until(
                    EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".pagination-button-current b"),
                                                     str(self.start_page))
                )
            except:
                LogUtil.error(f"actors page {self.start_page} not found")
                break

            current_page = driver.find_element(
                By.CSS_SELECTOR, ".pagination-button-current b")
            LogUtil.info(f"fetch actors page {current_page.text}")

            # analyze content
            actor_list = driver.find_elements(By.CSS_SELECTOR, 'a.user-card')
            actor_infos = []
            for actor_node in actor_list:
                actor_info = self.calcActorInfo(actor_node)
                actor_infos.append(actor_info)

            self.processActors(actor_infos, driver.current_url)

            # next page
            next_btn = driver.find_element(
                By.CSS_SELECTOR, '.pagination-button-after-current')
            if next_btn is None:
                print(
                    f"no next button, page {current_page.text} is the last page")
                break

            if not self.DownloadLimit().moreActor():
                break

            self.start_page += 1

            # js click
            driver.execute_script("arguments[0].click();", next_btn)
            # wait
            # driver.implicitly_wait(2)
            time.sleep(3)

        if item.start_page >= 0:
            CacheUtil.setValue(CacheKey.CustomPage, self.start_page)
            LogUtil.info(f"set custom page to {self.start_page}")

        # driver.quit()
        return True
