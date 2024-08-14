import bs4.element
from bs4 import BeautifulSoup

from Consts import WorkerType, QueueType
from Utils import LogUtil
from Ctrls import DbCtrl, ResCtrl, PostCtrl, RequestCtrl
from Models.BaseModel import ResType
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import PostExtraInfo
from WorkQueue.PageQueueItem import PageQueueItem
from Workers.BaseWorker import BaseWorker


class AnalysePostWorker(BaseWorker):
    """
    worker to analyse post detail and extract resources
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__(worker_type=WorkerType.AnalysePost, task=task)

    def _queueType(self) -> QueueType:
        return QueueType.AnalysePost

    def __processElement(self, ele: bs4.element.Tag, extra_info: PostExtraInfo) -> str:
        href: str = ele.a['href']
        # error defence
        if href.endswith("f=undefined"):
            LogUtil.warn(f"{extra_info} undefined res")
            return None
        return RequestCtrl.formatFullUrl(href)

    def _process(self, item: PageQueueItem) -> bool:
        with DbCtrl.getSession() as session, session.begin():
            if item.content is None:
                return False
            extra_info: PostExtraInfo = item.extra_info

            soup = BeautifulSoup(item.content, features='html.parser')

            url_list = []
            image_list = soup.select('.post__thumbnail')
            for image in image_list:
                url = self.__processElement(image, extra_info)
                if url is not None:
                    url_list.append((ResType.Image, url))

            video_list = soup.select('.post__attachment')
            for video in video_list:
                url = self.__processElement(video, extra_info)
                if url is not None:
                    url_list.append((ResType.Video, url))

            post = PostCtrl.getPost(session, extra_info.post_id)
            # mark the post as analysed
            post.completed = True

            if len(url_list) == 0:
                return True

            # add records for the resources
            ResCtrl.addAllRes(session, extra_info.post_id, url_list)
            # enqueue all resources of the post
            QueueUtil.enqueueAllRes(self.QueueMgr(), extra_info.actor_info, post, self.DownloadLimit())

            return True
