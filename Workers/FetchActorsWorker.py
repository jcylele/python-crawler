import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Consts import WorkerType, QueueType
from Ctrls import ActorCtrl, DbCtrl
from Models.ActorInfo import ActorInfo
from WorkQueue import QueueUtil
from WorkQueue.BaseQueueItem import BaseQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker


class FetchActorsWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchActors, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchActors

    def processActors(self, actor_infos: list[ActorInfo]):
        with DbCtrl.getSession() as session, session.begin():
            for actor_info in actor_infos:
                # it's not the best place, but okay
                QueueUtil.enqueueActorIcon(self.QueueMgr(), actor_info)
                # enqueue actor if not exists
                if not ActorCtrl.hasActor(session, actor_info.actor_name) \
                        and self.DownloadLimit().moreActor(True):
                    ActorCtrl.addActor(session, actor_info)
                    QueueUtil.enqueueFetchActor(self.QueueMgr(), actor_info.actor_name)

    def _process(self, item: BaseQueueItem) -> bool:
        self.driver.get("https://coomer.party/artists")
        for i in range(1, 1000000):
            # wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "li.pagination-button-current b"), f"{i}")
            )
            # wait for status
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element((By.ID, "display-status"), "Displaying search results")
            )

            # analyze content
            actor_list = self.driver.find_elements(By.CSS_SELECTOR, 'a.user-card')
            actor_infos = []
            for actor_node in actor_list:
                actor_info = ActorInfo()
                href_list = actor_node.get_attribute("href").split("/")
                actor_info.actor_platform = href_list[1]
                actor_info.actor_link = href_list[3]

                actor_name_node = actor_node.find_element(By.CLASS_NAME, "user-card__name")
                if actor_name_node is None:
                    continue
                actor_name = actor_name_node.text
                if actor_name is None or len(actor_name) == 0:
                    continue

                actor_info.actor_name = actor_name
                actor_infos.append(actor_info)

            self.processActors(actor_infos)

            # next page
            next_btn = self.driver.find_element(By.CSS_SELECTOR, '.pagination-button-after-current')
            if next_btn is None:
                print(f"no next button, page {i} is the last page")
                break

            if not self.DownloadLimit().moreActor(False):
                break

            # js click
            self.driver.execute_script("arguments[0].click();", next_btn)
            # wait
            # driver.implicitly_wait(2)
            time.sleep(1)

        # self.driver.quit()
        return True
