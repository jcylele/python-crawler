from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Generic, TypeVar, Optional

import LogUtil
from Steps.InputConverters import getConverter

T = TypeVar('T')


class MainOperation(Enum):
    DownOne = auto()
    DownLiked = auto()
    DownSample = auto()
    LikeAll = auto()

    @property
    def Desc(self):
        if self == MainOperation.DownOne:
            return "download almost all posts of one actor"
        elif self == MainOperation.DownLiked:
            return "download some posts of all actors you liked"
        elif self == MainOperation.DownSample:
            return "download few samples of new actors"
        elif self == MainOperation.LikeAll:
            return "mark all remain actors as liked"
        return None

    @staticmethod
    def formatMainOperationTip():
        str_list = []
        for op in MainOperation:
            str_list.append(f"[{op.value}] {op.Desc}")
        str_list.append("input your operation number: ")
        return str_list


class BaseStep(ABC):
    @abstractmethod
    def addNextStep(self, next_step: 'BaseStep' | tuple[any, 'BaseStep']) -> 'BaseStep':
        raise NotImplementedError("subclasses of BaseStep must implement method addNextStep")

    @abstractmethod
    def getNextStep(self, next_key: any) -> 'BaseStep':
        raise NotImplementedError("subclasses of BaseStep must implement method getNextStep")

    def execute(self, data: any, last_input: any = None):
        LogUtil.info(f"{self} execute")
        next_key = self._innerExecute(data, last_input)
        next_step = self.getNextStep(next_key)
        if next_step is None:
            return

        return next_step.execute(data, next_key)

    @abstractmethod
    def _innerExecute(self, data: any, last_input: any) -> any:
        raise NotImplementedError("subclasses of BaseStep must implement method _innerExecute")


class EndStep(BaseStep):
    def __init__(self):
        super().__init__()

    def _innerExecute(self, data: any, last_input: any) -> any:
        pass

    def getNextStep(self, next_key: any) -> 'BaseStep':
        return None

    def addNextStep(self, next_step: 'BaseStep' | tuple[any, 'BaseStep']) -> 'BaseStep':
        raise RuntimeError(f"{self} can't addNextStep")

    def __repr__(self):
        return f"EndStep()"


class BaseLinearStep(BaseStep, ABC):
    def __init__(self):
        self.__next_step: Optional[BaseStep] = None

    def addNextStep(self, next_step: 'BaseStep') -> 'BaseStep':
        if isinstance(next_step, tuple):
            raise TypeError(f"invalid next_step: {next_step} in addNextStep of {self}")
        self.__next_step = next_step
        return self

    def getNextStep(self, next_key: any) -> 'BaseStep':
        return self.__next_step


class SetFieldStep(BaseLinearStep):
    def __init__(self, field_name: str):
        super(SetFieldStep, self).__init__()
        self.__field_name: str = field_name

    def _innerExecute(self, data: any, last_input: any):
        data[self.__field_name] = last_input
        return last_input

    def __repr__(self):
        return f"SetFieldStep({self.__field_name})"


class InputStep(BaseLinearStep, (Generic[T])):
    def __init__(self, tip: str | [str], input_type: typing.Type = str):
        super().__init__()
        self.__tip = tip
        self.__input_type = input_type

    def __showTip(self):
        if isinstance(self.__tip, str):
            LogUtil.info(self.__tip)
        else:
            for tip in self.__tip:
                LogUtil.info(tip)

    def _innerExecute(self, data: any, last_input: any) -> any:
        self.__showTip()
        str_input = input('>')

        next_key = getConverter(self.__input_type).convertInput(str_input)
        if next_key is None:
            raise Exception(f"invalid input {str_input} for {self.__input_converter}")

        return next_key

    def __repr__(self):
        return f"InputStep({self.__tip})"


class BranchStep(BaseStep, Generic[T]):
    def __init__(self):
        super().__init__()
        self.__next_dict: dict[T, 'BaseStep'] = {}

    def _innerExecute(self, data: any, last_input: T) -> T:
        return last_input

    def addNextStep(self, next_step: tuple[T, 'BaseStep']) -> BaseStep:
        if not isinstance(next_step, tuple):
            raise TypeError(f"invalid next_step: {next_step} in addNextStep of {self}")
        if next_step[0] in self.__next_dict:
            raise RuntimeError(f"duplicate key for next step {next_step[0]}")
        self.__next_dict[next_step[0]] = next_step[1]
        return self

    def getNextStep(self, next_key: T) -> 'BaseStep':
        if next_key not in self.__next_dict:
            raise RuntimeError(f"next key {next_key} not in {self}")
        return self.__next_dict.get(next_key)

    def __repr__(self):
        return f"BranchStep()"
