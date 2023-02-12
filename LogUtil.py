import datetime
from enum import Enum, auto

from colorama import Fore


class LogLv(Enum):
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
    global __UseList
    __UseList = use


def setMinLogLv(lv: LogLv):
    global __CurLogLv
    __CurLogLv = lv


def printLogList():
    for log in __LogList:
        print(f"{__LogColors[log[0]]}[{log[1]}] {log[2]}")
    __LogList.clear()


def __print(lv: LogLv, o):
    if lv.value < __CurLogLv.value:
        return
    str_time = datetime.datetime.now().strftime('%H:%M:%S')
    if __UseList:
        __LogList.append((lv, str_time, str(o)))
    else:
        print(f"{__LogColors[lv]}[{str_time}] {str(o)}")


def debug(msg: str):
    __print(LogLv.Debug, msg)


def info(msg: str):
    __print(LogLv.Info, msg)


def warn(msg: str):
    __print(LogLv.Warn, msg)


def error(msg: str):
    __print(LogLv.Error, msg)
