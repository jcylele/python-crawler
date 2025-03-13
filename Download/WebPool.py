import os
import threading

from selenium import webdriver

from Consts import WorkerType
from Download.WebQueue import WebQueue

__MaxDriverCount = {
    WorkerType.FetchActors: 1,
    WorkerType.FetchActorLink: 1,
    WorkerType.FetchActor: 2,
    WorkerType.FetchPost: 4,
}

__queue_dict: dict[WorkerType, WebQueue] = {}

__queue_lock = threading.Lock()


def __getQueue(worker_type: WorkerType) -> WebQueue:
    with __queue_lock:
        q = __queue_dict.get(worker_type, None)
        if q is None:
            q = WebQueue(__MaxDriverCount.get(worker_type))
            __queue_dict[worker_type] = q
        return q


def getDriver(worker_type: WorkerType) -> webdriver.Chrome:
    # LogUtil.info(f"get driver of {worker_type}")
    q = __getQueue(worker_type)
    return q.get()


def releaseDriver(driver: webdriver.Chrome, worker_type: WorkerType):
    # LogUtil.info(f"release driver of {worker_type}")
    q = __getQueue(worker_type)
    q.put(driver)


def clearPool():
    # kill all web browser
    os.system("taskkill /f /t /im chrome.exe")
    # clear reference
    __queue_dict.clear()
