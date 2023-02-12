from typing import List, Tuple

import bs4.element
from bs4 import BeautifulSoup

import Consts
import LogUtil
from Ctrls import CtrlUtil, ResCtrl, PostCtrl
from WorkQueue import QueueMgr, QueueUtil
from WorkQueue.ExtraInfo import PostExtraInfo
from WorkQueue.PageQueueItem import PageQueueItem
from Workers.BaseWorker import BaseWorker


class AnalysePostWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type=Consts.WorkerType.AnalysePost)

    def _queueType(self) -> QueueMgr.QueueType:
        return QueueMgr.QueueType.AnalysePost

    def __processElement(self, ele: bs4.element.Tag, extra_info: PostExtraInfo) -> str:
        href: str = ele.a['href']
        if href.endswith("f=undefined"):
            LogUtil.warn(f"{extra_info} undefined res")
            return None
        return Consts.RootUrl + href

    def _process(self, item: PageQueueItem) -> bool:
        with CtrlUtil.getSession() as session, session.begin():
            if item.content is None:
                return False
            extra_info: PostExtraInfo = item.extra_info

            soup = BeautifulSoup(item.content, features='html.parser')

            url_list = []
            image_list = soup.select('.post__thumbnail')
            for image in image_list:
                url = self.__processElement(image, extra_info)
                if url is not None:
                    url_list.append((True, url))

            video_list = soup.select('.post__attachment')
            for video in video_list:
                url = self.__processElement(video, extra_info)
                if url is not None:
                    url_list.append((False, url))

            # 标记已下载
            post = PostCtrl.getPost(session, extra_info.post_id)
            post.completed = True

            if len(url_list) == 0:
                return True

            # 添加资源记录
            ResCtrl.addAllRes(session, extra_info.post_id, url_list)
            session.flush()
            # 下载资源
            QueueUtil.enqueueAllRes(post)

            return True


