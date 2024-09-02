# utility function for logging

import logging
import os
from time import strftime

# Create a logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Create a formatter to define the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler to write logs to a file
os.makedirs("logs", exist_ok=True)
log_file_name = strftime("logs/%Y_%m_%d_%H_%M_%S.log")
file_handler = logging.FileHandler(log_file_name)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # You can set the desired log level for console output
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def debug(o: any):
    logger.debug(o)


def info(o: any):
    logger.info(o)


def warn(o: any):
    logger.warning(o)


def error(o: any):
    logger.error(o)
