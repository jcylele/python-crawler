import threading
import time
from time import sleep
from typing import List

import Consts
import LogUtil
from WorkQueue import QueueMgr
from Workers.BaseWorker import BaseWorker

ReportQueueInterval = 10


class Guarder(threading.Thread):
    def __init__(self):
        super().__init__()
        self.workers: List[BaseWorker] = []
        self.next_report_time = 0
        self.__done = False

    def run(self):
        # 启动所有worker
        for worker in self.workers:
            worker.start()
        # 合并输出日志
        LogUtil.useList(True)
        # 启动守护
        while True:
            sleep(0.05)
            LogUtil.printLogList()
            if not self.__done:
                self.checkWorkers()
                self.reportQueueSize()
                self.__done = self.isJobDone()
                if self.__done:
                    LogUtil.info("Done!!!")

    def isJobDone(self) -> bool:
        if not QueueMgr.empty():
            return False
        for worker in self.workers:
            if not worker.isWaiting():
                return False
        return True

    def reportQueueSize(self):
        if self.next_report_time > time.time():
            return
        # Queue
        LogUtil.info(QueueMgr.report())
        # Worker
        wlist = {}
        for worker in self.workers:
            worker.reportDeath()
            if not worker.isWaiting():
                wt = worker.workerType().name
                if wt in wlist:
                    wlist[wt] += 1
                else:
                    wlist[wt] = 1
        LogUtil.info(f"working: {wlist}")

        self.next_report_time = time.time() + ReportQueueInterval

    def checkWorkers(self):
        for worker in self.workers:
            worker.reportDeath()

    def addWorker(self, worker: BaseWorker):
        self.workers.append(worker)
