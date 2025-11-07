import asyncio
from Consts import TaskType
from Download.DownloadTask import DownloadTask

next_task_id = 0
task_dict: dict[int, DownloadTask] = {}


def nextTaskId() -> int:
    global next_task_id
    next_task_id += 1
    return next_task_id


def NewTask(task_type: TaskType) -> DownloadTask:
    task_uid = nextTaskId()
    task = DownloadTask(task_uid, task_type)
    task_dict[task_uid] = task
    return task


def RemoveFinishedTasks():
    finished_task = []
    for task_uid, task in task_dict.items():
        if task.isDone():
            finished_task.append(task_uid)
    for task_uid in finished_task:
        del task_dict[task_uid]


def GetTaskCount() -> int:
    RemoveFinishedTasks()
    return len(task_dict)


def GetAllTask() -> list[DownloadTask]:
    RemoveFinishedTasks()
    return list(task_dict.values())


async def StopTask(task_uid: int):
    task = task_dict.get(task_uid)
    if task:
        await task.Stop()
        del task_dict[task_uid]


async def StopAllTasks():
    # 1. 收集所有需要执行的 Stop 协程到一个列表中
    #    注意：这里只是创建了协程对象，还没有执行它们
    stop_coroutines = [task.Stop() for task in task_dict.values()]

    # 2. 使用 asyncio.gather 并发运行所有 Stop 协程，并等待它们全部完成
    #    这就是您说的“统一等”
    await asyncio.gather(*stop_coroutines, return_exceptions=True)
    task_dict.clear()


def GetActorIds() -> list[int]:
    actor_ids = []
    for task in task_dict.values():
        actor_ids.extend(task.actor_ids)
    return actor_ids
