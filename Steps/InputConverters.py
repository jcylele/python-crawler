import typing


class BaseInputConverter(object):
    def convertInput(self, str_input: str) -> any:
        raise NotImplementedError("subclasses of BaseInputConverter must implement method convertInput")


class DefaultInputConverter(BaseInputConverter):
    def convertInput(self, str_input: str) -> str:
        return str_input


class IntEnumInputConverter(BaseInputConverter):
    def __init__(self, enum_type):
        super().__init__()
        self.__enum_type = enum_type

    def convertInput(self, str_input: str) -> any:
        try:
            return self.__enum_type(int(str_input))
        except:
            return None


class BoolInputConverter(BaseInputConverter):
    def convertInput(self, str_input: str) -> bool:
        if str_input == 'Y' or str_input == 'y':
            return True
        elif str_input == 'N' or str_input == 'n':
            return False
        return None


def getConverter(input_type: typing.Type):
    if input_type == bool:
        return BoolInputConverter()
    elif input_type == str:
        return DefaultInputConverter()
    else:  # Enum
        return IntEnumInputConverter(input_type)
