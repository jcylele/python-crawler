import Configs
from Consts import WorkerType
from Workers.BaseWorker import BaseWorker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BaseFetchWorker(BaseWorker):
    """
    base class for workers working through request
    """

    @staticmethod
    def createDriver(show: bool) -> webdriver.Chrome:
        if show:
            return webdriver.Chrome()
        else:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            return webdriver.Chrome(chrome_options)

    def __init__(self, worker_type: WorkerType, task: 'DownloadTask'):
        super().__init__(worker_type, task)
        self.driver = self.createDriver(Configs.SHOW_BROWSER)
