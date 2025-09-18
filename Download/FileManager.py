import asyncio
from typing import Dict
from threading import Lock as ThreadLock

# 1. 创建一个全局字典来存储文件路径到 asyncio.Lock 的映射
#    key: str (file_path) -> value: asyncio.Lock
__file_locks: Dict[str, asyncio.Lock] = {}

# 2. 创建一个线程锁 (threading.Lock)
#    这个锁的作用是保护 __file_locks 字典本身在多线程环境下的访问安全。
#    虽然我们的 worker 现在是协程，但 FastAPI 可能在多个线程中运行，
#    或者您可能在其他地方使用了 to_thread，所以保护这个全局字典是必要的。
__dict_lock = ThreadLock()

def get_lock(file_path: str) -> asyncio.Lock:
    """
    为指定的文件路径获取或创建一个 asyncio.Lock。
    这个函数是并发安全的。
    """
    # 3. 先快速检查，不加锁。这能提高已存在锁的获取性能。
    if file_path in __file_locks:
        return __file_locks[file_path]

    # 4. 如果锁可能不存在，则进入线程安全保护区
    with __dict_lock:
        # 5. 双重检查锁定 (Double-Checked Locking)
        #    在获取线程锁后，再次检查锁是否已被其他线程创建。
        #    这可以防止竞态条件下重复创建锁。
        lock = __file_locks.get(file_path)
        if lock is None:
            # 6. 如果确定锁不存在，则创建一个新的并存储起来
            lock = asyncio.Lock()
            __file_locks[file_path] = lock
        
        return lock
