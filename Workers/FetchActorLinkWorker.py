from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy.orm import Session

from Consts import WorkerType, QueueType
from Ctrls import ActorLinkCtrl, DbCtrl, RequestCtrl
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker


class FetchActorLinkWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchActorLink, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchActorLink

    @staticmethod
    def linkChecked(actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            ActorLinkCtrl.setActorLinkChecked(session, actor_id)

    def processLinks(self, actor_infos: list[ActorInfo], cur_url: str):
        with DbCtrl.getSession() as session, session.begin():
            ActorLinkCtrl.checkActorLink(session, actor_infos, self.init_category())

    def _loadSelector(self) -> str:
        return ".card-list__items"

    def _url(self, item: FetchActorQueueItem) -> str:
        actor_info = self.getActorInfo(item.actor_id)
        return RequestCtrl.formatActorLinksUrl(actor_info)

    def _checkFetch(self, session: Session, item: FetchActorQueueItem):
        return not ActorLinkCtrl.isLinkChecked(session, item.actor_id)

    def _onFetched(self, item: FetchActorQueueItem, driver: webdriver.Chrome) -> bool:
        actor_info = self.getActorInfo(item.actor_id)
        # actor icon
        self._saveActorIcon(actor_info, ".user-header__avatar img", driver, True)

        list_element = driver.find_element(By.CSS_SELECTOR, ".card-list__items")
        try:
            # no links
            list_element.find_element(By.CSS_SELECTOR, "p.card-list__item--no-results")
            FetchActorLinkWorker.linkChecked(item.actor_id)
            LogUtil.info(f"actor {actor_info.actor_name} has no links")
            return True
        except:
            pass

        actor_list = list_element.find_elements(By.CSS_SELECTOR, 'a.user-card')
        actor_infos = [actor_info]
        for actor_node in actor_list:
            info = self.calcActorInfo(actor_node)
            actor_infos.append(info)

        if len(actor_infos) == 1:
            LogUtil.error(f"actor {actor_info.actor_name} linked not found")
            return True

        self.processLinks(actor_infos, driver.current_url)

        return True
