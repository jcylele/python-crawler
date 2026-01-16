"""
Utility functions collection.
"""

import base64
import binascii
from datetime import datetime
import functools
import os
from pathlib import Path
import shutil
import sys
import time
import ffmpeg
from math import floor

from Consts import DateFormat
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


def stripToNone(value: str | None):
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


def get_media_info(file_path) -> tuple[int, int, int]:
    """获取视频/图片文件的基本信息"""
    try:
        # 获取视频流信息
        probe = ffmpeg.probe(file_path)
        streams = probe['streams']
        video_stream = None
        # 获取视频流
        for stream in streams:
            codec_type = stream.get('codec_type')
            if codec_type == 'video' or codec_type == 'image':
                video_stream = stream
                break
        # 没有视频流
        if video_stream is None:
            return 0, 0, 0
        # 基本信息
        width = int(video_stream['width'])  # 宽度
        height = int(video_stream['height'])  # 高度
        duration = floor(float(probe['format'].get('duration', 0)))

        return width, height, duration
    except Exception as e:
        LogUtil.error(f"get media info failed")
        LogUtil.exception(e)
        return 0, 0, 0


def get_project_root() -> Path:
    """从当前文件位置向上查找，直到找到包含 main.py 的目录作为项目根目录。"""
    current_path = Path(__file__).resolve()
    while True:
        if (current_path / 'main.py').exists():
            return current_path
        parent_path = current_path.parent
        if parent_path == current_path:
            # 到达文件系统的根目录了，还没找到
            raise FileNotFoundError("无法定位项目根目录。请确保 main.py 文件在项目根目录中。")
        current_path = parent_path


def fileCount(folder_path: str) -> int:
    path = Path(folder_path)
    if not path.exists():
        return 0
    if not path.is_dir():
        return 0

    try:
        thumbnail_count = len([f for f in path.iterdir() if f.is_file()])
        return thumbnail_count
    except PermissionError:
        LogUtil.error(f"no permission to access folder: {folder_path}")
        return 0


def formatStaticFile(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        
        # 1. 获取外部路径 (exe 同级目录)，这是我们希望保存用户配置的地方
        base_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(base_dir, relative_path)
        
        # 2. 获取内部路径 (PyInstaller 临时解压目录)，这是存放默认配置的地方
        bundle_dir = sys._MEIPASS
        internal_path = os.path.join(bundle_dir, relative_path)
        
        # 策略：如果是 json 配置文件，我们需要持久化，优先使用外部文件
        if relative_path.endswith('.json'):
            # 如果外部文件已经存在，直接使用外部文件 (保留了用户设置)
            if os.path.exists(external_path):
                return external_path
            
            # 如果外部文件不存在，但内部有默认值，则将默认值复制到外部 (初始化用户配置)
            if os.path.exists(internal_path):
                try:
                    # 确保目标文件夹存在
                    os.makedirs(os.path.dirname(external_path), exist_ok=True)
                    # 复制文件
                    shutil.copy2(internal_path, external_path)
                    # 返回外部路径，这样后续的读取/写入都会针对这个持久化文件
                    return external_path
                except Exception as e:
                    LogUtil.error(f"Failed to copy default config to external path: {e}")
                    # 如果复制失败(如权限问题)，降级使用内部临时文件
                    return internal_path

        # 对于非 json 文件 (如 js, 图片等静态资源)，通常只读，优先使用打包在内部的资源
        if os.path.exists(internal_path):
            return internal_path
            
        # 如果内部没有，尝试返回外部路径
        return external_path
    else:
        # we are running in a normal Python environment
        bundle_dir = get_project_root()

    # print(bundle_dir)
    return os.path.join(bundle_dir, relative_path)


def datetime_format(time: datetime, format: DateFormat) -> str:
    return time.strftime(format.value)

def format_now(format: DateFormat) -> str:
    return datetime.now().strftime(format.value)

def to_datetime(str_time: str, format: DateFormat) -> datetime:
    return datetime.strptime(str_time, format.value)


def to_date(str_time: str, format: DateFormat, is_begin: bool = False) -> datetime:
    date = to_datetime(str_time, format)
    if is_begin:
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return date
