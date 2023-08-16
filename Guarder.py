import threading
import time
from time import sleep
from typing import List

from Utils import LogUtil
from Workers import WorkerMgr
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
        while not self.done:
            sleep(0.0333)  # 30fps
            LogUtil.printAll()  # print cached logs
            self.checkWorkerTimeout()
            self.reportRunningStatus()
            if self.isJobDone():
                self.done = True
                LogUtil.info("Done!!!")
                for worker in self.workers:
                    worker.Stop()
                LogUtil.printAll()  # print cached logs

    def Stop(self):
        for worker in self.workers:
            worker.Stop()
        self.done = True

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

    def checkWorkerTimeout(self):
        new_workers = []
        for worker in self.workers:
            timeout = worker.getTimeout()
            if 0 < timeout < time.time():
                new_workers.append(WorkerMgr.createWorker(worker.workerType(), worker.task))
                worker.setTimeout(-1)
        for worker in new_workers:
            worker.start()
        self.workers.extend(new_workers)

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
