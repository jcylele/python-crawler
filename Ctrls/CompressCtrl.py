import zstandard

import Configs

__ResUriDecompressor: zstandard.ZstdDecompressor = None
__ResUriCompressor: zstandard.ZstdCompressor = None


def init():
    global __ResUriDecompressor
    global __ResUriCompressor

    with open(Configs.ResUriDictFilePath, mode='rb') as dict_file:
        dict_data_bytes = dict_file.read()
    dict_data = zstandard.ZstdCompressionDict(dict_data_bytes)

    __ResUriDecompressor = zstandard.ZstdDecompressor(dict_data=dict_data)
    __ResUriCompressor = zstandard.ZstdCompressor(dict_data=dict_data)


def encodeResUri(url: str) -> bytes:
    return __ResUriCompressor.compress(str.encode(url))


def decodeResUri(uri: bytes) -> str:
    return __ResUriDecompressor.decompress(uri).decode()
