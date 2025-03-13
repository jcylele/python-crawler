import time
from queue import LifoQueue

from selenium import webdriver

import Configs
from Utils import LogUtil


class WebQueue(object):
    def __init__(self, max_count: int):
        self.left_count = max_count
        self.__queue: LifoQueue[webdriver.Chrome] = LifoQueue()

    def get(self):
        if self.__queue.empty() and self.left_count > 0:
            self.left_count -= 1
            return WebQueue.createDriver()
        while True:
            # return self.__queue.get()
            # below code ensures a thread can get the same driver if put and get at the same time
            try:
                item = self.__queue.get(block=False)
                return item
            except:
                time.sleep(3)

    def put(self, driver: webdriver.Chrome):
        self.__queue.put(driver)

    @staticmethod
    def createDriver() -> webdriver.Chrome:
        LogUtil.info("create driver")
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.accept_insecure_certs = True
        if Configs.SHOW_BROWSER:
            pass
        else:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        return webdriver.Chrome(options=options)
