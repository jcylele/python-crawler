import threading
import time
from time import sleep

from Utils import LogUtil
from Download import WorkerMgr
from Workers.BaseWorker import BaseWorker


class Guarder(threading.Thread):
    """
    monitor and report running status of all workers and queues
    """

    def __init__(self, task):
        super().__init__()
        self.workers: list[BaseWorker] = []
        self.task = task
        self.done = False

    def run(self):
        # start all worker threads
        for worker in self.workers:
            worker.start()
        # loop
        while not self.done:
            sleep(1)  # check interval
            self.checkWorkerTimeout()
            if self.isJobDone():
                self.done = True
                LogUtil.info(f"{self.task} Done!!!")
                for worker in self.workers:
                    worker.Stop()

    def Stop(self):
        for worker in self.workers:
            worker.Stop()
        self.done = True

    def isJobDone(self) -> bool:
        """
        check if all tasks are down
        :return:
        """
        if not self.task.queue_mgr.empty():  # all queues are empty
            # print("queue not empty")
            return False
        for worker in self.workers:
            if not worker.isWaiting():  # all workers are waiting for job
                # print(f"{worker.workerType()} is working")
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

    def getWorkerCountMap(self) -> dict[str, int]:
        worker_count_dict = {}
        for worker in self.workers:
            if worker.is_alive() and not worker.isWaiting():
                wt = worker.workerType().name
                if wt in worker_count_dict:
                    worker_count_dict[wt] += 1
                else:
                    worker_count_dict[wt] = 1

        return worker_count_dict

    def addWorker(self, worker: BaseWorker):
        self.workers.append(worker)
