_using_files: dict[str, int] = {}


def useFile(file_path: str, user: int) -> bool:
    """
    mark a file as used
    """
    if file_path in _using_files:
        return False
    _using_files[file_path] = user
    return True


def releaseFile(file_path: str, user: int) -> bool:
    """
    release a file
    """
    if file_path not in _using_files:
        return False
    if _using_files[file_path] != user:
        return False
    del _using_files[file_path]
    return True
