"""
orientation related file name process
"""

_landscape_prefix = "l"
_portrait_prefix = "p"
_prefix_set = set([_landscape_prefix, _portrait_prefix])


def hasPrefix(file_name: str) -> bool:
    return file_name[0] in _prefix_set


def getPrefix(is_landscape: bool) -> str:
    return _landscape_prefix if is_landscape else _portrait_prefix


def checkPrefix(file_name: str, is_landscape: bool) -> bool:
    return file_name.startswith(getPrefix(is_landscape))


def allDirName() -> str:
    return "All"


def getDirName(is_landscape: bool) -> str:
    return "Landscape" if is_landscape else "Portrait"
