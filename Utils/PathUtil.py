"""
support file path in bundle and normal environment
"""
import os
import shutil
import sys
from pathlib import Path

from Utils import LogUtil


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
                    LogUtil.error(
                        f"Failed to copy default config to external path: {e}")
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


def getExecutablePath(executable_name: str) -> str:
    # 确定 ffprobe 路径（打包环境或开发环境）
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 打包环境：从 _internal/ 目录查找
        executable_path = os.path.join(sys._MEIPASS, f'{executable_name}.exe')
        if not os.path.exists(executable_path):
            LogUtil.warning(f"{executable_name} not found in bundled location")
            return None
    else:
        # 开发环境：使用系统 PATH 中的 ffprobe
        executable_path = executable_name
        if shutil.which('ffmpeg') is None:
            LogUtil.warning(f"{executable_name} not found in PATH")
            return None

    return executable_path
