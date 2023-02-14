from bs4 import BeautifulSoup

import Configs
from Consts import WorkerType
from Ctrls import ActorCtrl, PostCtrl, DbCtrl
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import ActorExtraInfo
from WorkQueue.PageQueueItem import PageQueueItem
from Workers.BaseWorker import BaseWorker


class AnalyseActorWorker(BaseWorker):
    """
    worker to analyse the post list page of an actor
    """

    def __init__(self):
        super().__init__(worker_type=WorkerType.AnalyseActor)

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.AnalyseUser

    def _process(self, item: PageQueueItem) -> bool:
        with DbCtrl.getSession() as session, session.begin():
            if item.content is None:
                return False
            extra_info: ActorExtraInfo = item.extra_info
            actor = ActorCtrl.addActor(session, extra_info.actor_name)

            soup = BeautifulSoup(item.content, features='html.parser')
            article_list = soup.select('article.post-card')
            for article in article_list:
                post_id = int(article['data-id'])
                post = PostCtrl.getPost(session, post_id)
                if post is None:
                    PostCtrl.addPost(session, extra_info.actor_name, post_id)
                    QueueUtil.enqueuePost(extra_info.actor_name, post_id, item.url)
                elif not post.completed:    # the post is not analysed yet
                    QueueUtil.enqueuePost(extra_info.actor_name, post_id, item.url)
                else:   # all resources of the post are already added
                    QueueUtil.enqueueAllRes(post)

            if len(article_list) > 0:  # last page reached
                start_order = extra_info.start_order + len(article_list)
                if start_order < Configs.MaxPostCount:
                    QueueUtil.enqueueActor(extra_info.actor_name, start_order, item.url)
            else:
                actor.completed = True

            return True
