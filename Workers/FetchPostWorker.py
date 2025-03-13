from selenium import webdriver
from selenium.webdriver.common.by import By

from Consts import WorkerType, QueueType, ResType
from Ctrls import DbCtrl, RequestCtrl, PostCtrl, ResCtrl
from Download import QueueUtil
from WorkQueue.FetchQueueItem import FetchPostQueueItem
from Workers.BaseFetchWorker import BaseFetchWorker


class FetchPostWorker(BaseFetchWorker):
    """
    worker to analyse the actor list page
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.FetchPost, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.FetchPost

    def _getResUrl(self, res_node):
        a_node = res_node.find_element(By.CSS_SELECTOR, "a")
        if a_node is None:
            return None
        href = a_node.get_attribute("href")
        # error defence
        if href.endswith("f=undefined"):
            # LogUtil.warn(f"{item} undefined res")
            return None

        return RequestCtrl.formatFullUrl(href)

    def _loadSelector(self) -> str:
        return ".post__body"

    def _url(self, item: FetchPostQueueItem) -> str:
        return RequestCtrl.formatPostUrl(item.actor_info, item.post_id, item.is_dm)

    def _checkFetch(self, item: FetchPostQueueItem):
        return self.hasActorFolder(item.actor_info.actor_id)

    def _onFetched(self, item: FetchPostQueueItem, driver: webdriver.Chrome) -> bool:
        # actor icon
        self._saveActorIcon(item.actor_info, ".post__user-profile img", driver, False)

        # analyze res
        url_list = []

        image_list = driver.find_elements(By.CSS_SELECTOR, '.post__thumbnail')
        for image_node in image_list:
            url = self._getResUrl(image_node)
            if url is not None:
                url_list.append((ResType.Image, url))

        video_list = driver.find_elements(By.CSS_SELECTOR, '.post__attachment')
        for video_node in video_list:
            url = self._getResUrl(video_node)
            if url is not None:
                url_list.append((ResType.Video, url))

        # write to db, enqueue items
        with DbCtrl.getSession() as session, session.begin():
            post = PostCtrl.getPost(session, item.post_id)

            if len(url_list) > 0:
                # add records for the resources
                ResCtrl.addAllRes(session, item.post_id, url_list)
                # enqueue all resources of the post
                QueueUtil.enqueueAllRes(self.QueueMgr(), item.actor_info, post, self.DownloadLimit())

            # mark the post as analysed
            post.completed = True

        return True
