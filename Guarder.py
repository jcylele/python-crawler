import threading
import time
from time import sleep
from typing import List

from Utils import LogUtil
from Workers.BaseWorker import BaseWorker

ReportQueueInterval = 10


class Guarder(threading.Thread):
    """
    monitor and report running status of all workers and queues
    """

    def __init__(self, task: 'DownloadTask'):
        super().__init__()
        self.workers: List[BaseWorker] = []
        self.next_report_time = 0
        self.task = task
        self.done = False

    def run(self):
        # start all worker threads
        for worker in self.workers:
            worker.start()
        # thread put log messages in a list instead of printing them out
        # maybe it can boost the speed of threads
        LogUtil.useList(True)
        # loop
        while True:
            sleep(0.0333)  # 30fps
            LogUtil.printAll()  # print cached logs
            self.reportRunningStatus()
            if self.isJobDone():
                self.done = True
                LogUtil.info("Done!!!")
                for worker in self.workers:
                    worker.Stop()
                LogUtil.printAll()  # print cached logs
                break

    def isJobDone(self) -> bool:
        """
        check if all tasks are down
        :return:
        """
        if not self.task.queueMgr.empty():  # all queues are empty
            return False
        for worker in self.workers:
            if not worker.isWaiting():  # all workers are waiting for job
                return False
        return True

    def reportRunningStatus(self):
        """
        report queues' size and running worker count
        :return:
        """
        if self.next_report_time > time.time():
            return
        # Task
        LogUtil.info(self.task)
        # Queue
        LogUtil.info(self.task.queueMgr.runningReport())
        # Worker
        worker_count_dict = {}
        for worker in self.workers:
            if worker.is_alive() and not worker.isWaiting():
                wt = worker.workerType().name
                if wt in worker_count_dict:
                    worker_count_dict[wt] += 1
                else:
                    worker_count_dict[wt] = 1
        LogUtil.info(f"working: {worker_count_dict}")

        self.next_report_time = time.time() + ReportQueueInterval

    def addWorker(self, worker: BaseWorker):
        self.workers.append(worker)
