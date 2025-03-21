# Data Models consistent with table structs in database
import json
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase


class IntEnum(sa.types.TypeDecorator):
    """
    convert between enum in python and integer in database
    """

    impl = sa.Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        """
        from python to database
        """
        return value.value

    def process_result_value(self, value, dialect):
        """
        from database to python
        """
        return self._enumtype(value)


class BaseModelEncoder(json.JSONEncoder):
    """
    json encoder for BaseModel
    """

    def default(self, obj):
        # custom toJson
        method = getattr(obj, 'toJson', None)
        if callable(method):
            return method()
        # enum value
        if isinstance(obj, Enum):
            return obj.value
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class BaseModel(DeclarativeBase):
    def toJson(self):
        json_data = {}
        for c in self.__table__.columns:
            attr = getattr(self, c.name)
            if isinstance(attr, Enum):
                attr = attr.value

            if attr is not None:
                json_data[c.name] = attr

        return json_data



