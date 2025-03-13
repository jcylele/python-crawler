import os
import time

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import Configs
from Consts import WorkerType
from Ctrls import DbCtrl, ActorCtrl
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from Download import WebPool, QueueUtil
from WorkQueue.BaseQueueItem import BaseQueueItem
from Workers.BaseWorker import BaseWorker
from Workers.ImageCompleteWait import ImageCompleteWait


class BaseFetchWorker(BaseWorker):
    """
    base class for workers working through webdriver
    """

    def __init__(self, worker_type: WorkerType, task: 'DownloadTask'):
        super().__init__(worker_type, task)

    def getActorInfo(self, actor_id: int) -> ActorInfo:
        with DbCtrl.getSession() as session, session.begin():
            return ActorCtrl.getActorInfo(session, actor_id)

    def calcActorInfo(self, actor_node: WebElement) -> ActorInfo:
        href_list = actor_node.get_attribute("href").split("/")

        actor_info = ActorInfo()
        actor_info.actor_platform = href_list[-3]
        actor_info.actor_link = href_list[-1]

        actor_name_node = actor_node.find_element(By.CLASS_NAME, "user-card__name")
        if actor_name_node is None:
            raise Exception(f"actor name element not found")
        actor_name = actor_name_node.text
        actor_info.actor_name = actor_name

        return actor_info

    def _saveActorIcon(self, actor_info: ActorInfo, selector: str, driver: webdriver.Chrome, enqueue: bool):
        """
        fetch actor icon if not exists, screenshot icon for temporary use if not exists
        """
        # real icon
        if os.path.exists(actor_info.icon_file_path()):
            return

        # fetch real icon
        if enqueue:
            QueueUtil.enqueueActorIcon(self.QueueMgr(), actor_info, driver.current_url)

        # screenshot icon
        icon_ss_file_path = actor_info.icon_ss_file_path()
        if os.path.exists(icon_ss_file_path):
            return
        # take screenshot
        try:
            WebDriverWait(driver, 15).until(ImageCompleteWait(selector))
            driver.find_element(By.CSS_SELECTOR, selector).screenshot(icon_ss_file_path)
        except:
            LogUtil.info(f"head icon of {actor_info.actor_name} not loaded")

    def _onFetched(self, item: BaseQueueItem, driver: webdriver.Chrome) -> bool:
        raise NotImplementedError("subclasses of BaseFetchWorker must implement method _onFetched")

    def _loadSelector(self) -> str:
        raise NotImplementedError("subclasses of BaseFetchWorker must implement method _loadSelector")

    def _url(self, item: BaseQueueItem) -> str:
        raise NotImplementedError("subclasses of BaseFetchWorker must implement method _url")

    def _checkFetch(self, item: BaseQueueItem):
        raise NotImplementedError("subclasses of BaseFetchWorker must implement method _checkFetch")

    def _process(self, item: BaseQueueItem) -> bool:
        if not self._checkFetch(item):
            return True
        driver = WebPool.getDriver(self.workerType())
        driver.get(self._url(item))
        for i in range(30):
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self._loadSelector()))
                )
            except:
                title = driver.title
                LogUtil.info(f"failed to load {item}, get {title} instead")
                # just release the driver
                if not Configs.SHOW_BROWSER:
                    WebPool.releaseDriver(driver, self.workerType())
                    return False
                if "DDoS-Guard" in title:
                    # wait for human
                    time.sleep(10)
                elif "Error" in title:
                    # refresh page
                    time.sleep(10)
                    driver.refresh()

        processed = self._onFetched(item, driver)
        WebPool.releaseDriver(driver, self.workerType())
        return processed
