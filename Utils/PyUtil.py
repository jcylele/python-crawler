import base64
import binascii
import functools
import time

from Utils import LogUtil


def decodeBase64(b64string):
    padding = 4 - (len(b64string) % 4) if len(b64string) % 4 else 0
    padded_b64string = b64string + '=' * padding
    return base64.urlsafe_b64decode(padded_b64string).decode('utf-8')


def encodeBase64(string):
    return base64.urlsafe_b64encode(string.encode('utf-8')).decode('utf-8')


def hex2bytes(hex_string):
    return binascii.unhexlify(hex_string)


def bytes2hex(bytes_data):
    return binascii.hexlify(bytes_data).decode('ascii')


def stripToNone(value: str):
    if value is None:
        return None
    value = value.strip()
    if len(value) == 0:
        return None
    return value

def time_cost(func):
    """
    一个简单的装饰器，用于计算并打印函数的执行时间。
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        cost = (end_time - start_time) * 1000
        
        log_msg = f"Function '{func.__name__}' executed in {cost:.2f} ms"
        LogUtil.info(log_msg)
        
        return result
    return wrapper