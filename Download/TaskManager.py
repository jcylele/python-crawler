from Download.DownloadTask import DownloadTask

next_task_id = 0
task_dict: dict[int, DownloadTask] = {}


def nextTaskId() -> int:
    global next_task_id
    next_task_id += 1
    return next_task_id


def NewTask() -> DownloadTask:
    task_uid = nextTaskId()
    task = DownloadTask(task_uid)
    task_dict[task_uid] = task
    return task


def GetAllTask() -> list[DownloadTask]:
    finished_task = []
    for task_uid, task in task_dict.items():
        if task.isDone():
            finished_task.append(task_uid)
    for task_uid in finished_task:
        del task_dict[task_uid]
    return list(task_dict.values())


def StopTask(task_uid: int):
    task = task_dict.get(task_uid)
    if task:
        task.Stop()
        del task_dict[task_uid]
