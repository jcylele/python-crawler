# utility function for logging

import logging
import os
from time import strftime

# Create a formatter to define the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler to write logs to a file
os.makedirs("logs", exist_ok=True)
log_file_name = strftime("logs/%Y_%m_%d_%H_%M_%S.log")
file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)


# logger for general purpose
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
logger.propagate = False  # 阻止日志消息向上传播

logger.addHandler(file_handler)
logger.addHandler(console_handler)

if False:
    # 配置 SQLAlchemy 的日志记录器，使其也写入日志文件
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.DEBUG)  # INFO 级别记录SQL语句，DEBUG 级别会包含参数
    sqlalchemy_logger.propagate = False  # 阻止向上传播，避免重复
    sqlalchemy_logger.addHandler(file_handler)  # 添加到文件
    sqlalchemy_logger.addHandler(console_handler)  # 也输出到控制台（可选）


def exception(e: BaseException):
    logger.exception(e)


def debug(o: any):
    logger.debug(o)


def info(o: any):
    logger.info(o)


def warning(o: any):
    logger.warning(o)


def error(o: any):
    logger.error(o)
