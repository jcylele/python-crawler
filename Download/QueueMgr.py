# manager for queues

import asyncio

from Consts import QueueType
from WorkQueue.BaseQueueItem import BaseQueueItem, SentinelQueueItem
from routers.schemas_others import CommonCount


class QueueMgr(object):
    """
    manager for queues
    """

    def __init__(self):
        self.__all_queues: dict[QueueType, asyncio.Queue] = {}
        self.__worker_count_map: dict[QueueType, int] = {}
        self.__lock = asyncio.Lock()
        for queue_type in QueueType:
            self.__worker_count_map[queue_type] = 0
            if queue_type > QueueType.MinPriorityQueue:
                self.__all_queues[queue_type] = asyncio.PriorityQueue()
            else:
                self.__all_queues[queue_type] = asyncio.Queue()

    async def wait_for_finish(self):
        while True:
            await asyncio.gather(*[q.join() for q in self.__all_queues.values()])
            async with self.__lock:
                if all(count == 0 for count in self.__worker_count_map.values()):
                    break
            await asyncio.sleep(1)

    def empty(self) -> bool:
        """
        is all queues empty
        :return:
        """
        for q in self.__all_queues.values():
            if not q.empty():
                return False
        return True

    def get_queue_counts(self) -> list[CommonCount]:
        count_list = []
        for q_type, q in self.__all_queues.items():
            if not q.empty():
                count_list.append(CommonCount(
                    name=q_type.name, count=q.qsize()))
        return sorted(count_list, key=lambda x: x.name)

    def get_worker_counts(self) -> list[CommonCount]:
        count_list = []
        for q_type, count in self.__worker_count_map.items():
            if count > 0:
                count_list.append(CommonCount(name=q_type.name, count=count))
        return sorted(count_list, key=lambda x: x.name)

    async def put(self, queue_type: QueueType, item: BaseQueueItem):
        """
        put queue item into the queue.
        """
        await self.__all_queues[queue_type].put(item)
        # LogUtil.info(f"put item {item} into queue {queue_type.name}")

    async def get(self, queue_type: QueueType) -> BaseQueueItem:
        """
        get an item from the queue, wait if the queue is empty
        """

        item = await self.__all_queues[queue_type].get()
        # LogUtil.info(f"get item {item} from queue {queue_type.name}")
        return item

    def item_done(self, queue_type: QueueType):
        self.__all_queues[queue_type].task_done()

    async def add_worker(self, queue_type: QueueType):
        async with self.__lock:
            self.__worker_count_map[queue_type] += 1

    async def remove_worker(self, queue_type: QueueType):
        async with self.__lock:
            self.__worker_count_map[queue_type] -= 1

    async def enqueueSentinel(self, queue_type: QueueType):
        await self.put(queue_type, SentinelQueueItem())
