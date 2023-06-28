# utility function for logging

import datetime
from enum import Enum, auto

from colorama import Fore


class LogLv(Enum):
    """
    log levels, order is important because values will be compared
    """
    Debug = auto()
    Info = auto()
    Warn = auto()
    Error = auto()


__UseList = False
__LogList = []
__CurLogLv = LogLv.Debug

__LogColors = {
    LogLv.Debug: Fore.BLUE,
    LogLv.Info: Fore.LIGHTWHITE_EX,
    LogLv.Warn: Fore.YELLOW,
    LogLv.Error: Fore.RED,
}


def useList(use: bool):
    """
    set whether to use a list to print log in batch
    :param use:
    :return:
    """
    global __UseList
    __UseList = use


def setMinLogLv(lv: LogLv):
    """
    skip log levels which are less than lv
    :param lv:
    :return:
    """
    global __CurLogLv
    __CurLogLv = lv


def __realPrint(lv: LogLv, str_time: str, str_o: str):
    """
    actual print function
    :param lv: log level which is used to change the color
    :param str_time: time stamp
    :param str_o: print content
    :return:
    """
    print(f"{__LogColors[lv]}[{str_time}] {str_o}")


def printAll():
    """
    print all cached logs and clear the log cache
    :return:
    """
    tmp = __LogList.copy()
    __LogList.clear()
    for log in tmp:
        __realPrint(*log)


def __print(lv: LogLv, o: any):
    # filter log level
    if lv.value < __CurLogLv.value:
        return
    # add time stamp
    str_time = datetime.datetime.now().strftime('%H:%M:%S')
    if __UseList:
        __LogList.append((lv, str_time, str(o)))
    else:
        __realPrint(lv, str_time, str(o))


def debug(o: any):
    __print(LogLv.Debug, o)


def info(o: any):
    __print(LogLv.Info, o)


def warn(o: any):
    __print(LogLv.Warn, o)


def error(o: any):
    __print(LogLv.Error, o)
