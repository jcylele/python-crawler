import random
import shutil
import time

import Configs
from Consts import WorkerType
from Ctrls import RequestCtrl
from Utils import LogUtil
from WorkQueue.UrlQueueItem import UrlQueueItem
from Workers.BaseWorker import BaseWorker

average_wait_time = 1


class BaseRequestWorker(BaseWorker):
    """
    base class for workers working through request
    """

    def __init__(self, worker_type: WorkerType, task: 'DownloadTask'):
        super().__init__(worker_type, task)
        self.requestSession = RequestCtrl.createRequestSession()

    def _onException(self, item, e: BaseException):
        super()._onException(item, e)
        # fake a new session
        self.requestSession = RequestCtrl.createRequestSession()

    def _sleep(self):
        time.sleep(random.random() * 2 * average_wait_time)

    def _head(self, item: UrlQueueItem) -> (bool, int):
        """
        get size of a web resource
        :return (succeed or not, size of the resource)
        """
        self._sleep()
        # set the last url, some websites check for it
        self.requestSession.headers["referer"] = item.from_url
        try:
            res = self.requestSession.head(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return False, 0

        if res.status_code == 200:
            content_length = res.headers.get('Content-Length')
            if content_length is None:
                return True, 0
            return True, int(content_length)
        elif res.status_code == 302:  # redirect
            item.from_url = item.url
            url = res.headers['Location']
            item.url = RequestCtrl.formatFullUrl(url)
            return self._head(item)
        elif res.status_code == 429 or res.status_code == 403:  # too fast
            time.sleep(5)
            LogUtil.warn(f"head {item.extra_info} too fast")
            return self._head(item)
        else:
            LogUtil.info(f"head error {res.status_code}: {item.url}")
            return False, 0

    def _download(self, item: UrlQueueItem) -> str:
        """
        download the web page
        """

        self._sleep()
        # set the last url, some websites check for it
        self.requestSession.headers["referer"] = item.from_url
        try:
            res = self.requestSession.get(item.url, allow_redirects=False)
        except BaseException as e:
            LogUtil.error(e)
            return None

        if res.status_code == 200:
            return res.text
        elif res.status_code == 302:  # redirect
            item.from_url = item.url
            url = res.headers['Location']
            item.url = RequestCtrl.formatFullUrl(url)
            return self._download(item)
        elif res.status_code == 429:  # too fast
            time.sleep(5)
            LogUtil.warn(f"get {item.extra_info} too fast")
            return self._download(item)
        else:
            LogUtil.info(f"get error {res.status_code}: {item.url}")
            return None

    def _downloadStream(self, url: str, file_path: str, file_mode: str = "wb"):
        self._sleep()
        with self.requestSession.get(url, stream=True) as r:
            with open(file_path, file_mode) as f:
                # write stream data into file, the most efficient way of download that I know
                shutil.copyfileobj(r.raw, f)
