from playwright.async_api import Page, Response
from sqlalchemy.orm import Session

from Consts import WorkerType
from Ctrls import ActorLinkCtrl, DbCtrl, RequestCtrl
from Models.ActorInfo import ActorInfo
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem
from Workers.ImageWait.ActorIconWait import ActorIconWait
from Workers.BaseFetchWorker import BaseFetchWorker


class FetchActorLinkWorker(BaseFetchWorker):
    """
    worker to analyse the actor link page
    """

    def __init__(self, task):
        super().__init__(worker_type=WorkerType.FetchActorLink, task=task)
        self.actor_info: ActorInfo | None = None
        self.actor_icon_wait = ActorIconWait()

    @staticmethod
    def linkChecked(actor_id: int):
        with DbCtrl.getSession() as session, session.begin():
            ActorLinkCtrl.setActorLinkChecked(session, actor_id)

    def processLinks(self, actor_infos: list[ActorInfo], cur_url: str):
        with DbCtrl.getSession() as session, session.begin():
            ActorLinkCtrl.checkActorLink(
                session, actor_infos, self.init_category())

    def _loadSelector(self) -> str:
        return ".card-list__items"

    def _url(self, item: FetchActorQueueItem) -> str:
        return RequestCtrl.formatActorLinksUrl(self.actor_info)

    def _checkFetch(self, session: Session, item: FetchActorQueueItem):
        return not ActorLinkCtrl.isLinkChecked(session, item.actor_id)

    def _beforeFetch(self, session: Session, item: FetchActorQueueItem):
        self.actor_info = self.getActorInfo(item.actor_id)
        self.actor_icon_wait.set_actor_info(self.actor_info)

    async def on_response(self, response: Response):
        await self.actor_icon_wait.on_response(response)

    async def _onFetched(self, item: FetchActorQueueItem, page: Page) -> bool:
        # actor icon
        await self.actor_icon_wait.wait(page)

        list_element = page.locator(".card-list__items")

        # no links
        no_result_locator = list_element.locator(
            "p.card-list__item--no-results")
        if (await no_result_locator.count()) > 0:
            FetchActorLinkWorker.linkChecked(item.actor_id)
            LogUtil.info(f"actor {self.actor_info.actor_name} has no links")
            return True

        actor_list = await list_element.locator('a.user-card').all()
        actor_infos = [self.actor_info]
        for actor_locator in actor_list:
            info = await self.calcActorInfo(actor_locator)
            actor_infos.append(info)

        if len(actor_infos) == 1:
            LogUtil.error(
                f"actor {self.actor_info.actor_name} linked not found")
            return True

        self.processLinks(actor_infos, page.url)

        return True
