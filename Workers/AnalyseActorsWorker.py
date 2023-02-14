from bs4 import BeautifulSoup

import Configs
from Consts import WorkerType
from Ctrls import ActorCtrl, DbCtrl
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ActorsExtraInfo
from WorkQueue.PageQueueItem import PageQueueItem
from Workers.BaseWorker import BaseWorker


class AnalyseActorsWorker(BaseWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self):
        super().__init__(worker_type=WorkerType.AnalyseActors)

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.AnalyseActors

    def _process(self, item: PageQueueItem) -> bool:
        with DbCtrl.getSession() as session, session.begin():
            if item.content is None:
                return False
            extra_info: ActorsExtraInfo = item.extra_info

            # extract actors from web content
            soup = BeautifulSoup(item.content, features='html.parser')
            actor_list = soup.select('article.user-card')
            actor_count = 0
            for actor_node in actor_list:
                actor_name = actor_node.get('data-id')
                if actor_name is None:
                    continue
                actor_count += 1
                if not ActorCtrl.hasActor(session, actor_name) \
                        and Configs.moreActor(True):
                    QueueUtil.enqueueActor(actor_name, 0, item.url)

            # next page
            if actor_count > 0 and Configs.moreActor(False):
                start_order = extra_info.start_order + actor_count
                QueueUtil.enqueueActors(start_order, item.url)

            return True
