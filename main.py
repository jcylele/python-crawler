import os
import time


def printTime():
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


cached = {}


def getCached(len1: int, len2: int):
    if len1 not in cached:
        cached[len1] = {}
    c1 = cached[len1]
    if len2 not in c1:
        c2 = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]
        c1[len2] = c2
    else:
        c2 = c1[len2]
        for i in range(len1 + 1):
            for j in range(len2 + 1):
                c2[i][j] = 0
    return c2


def lcs(x: str, y: str):
    """
    longest common subsequence
    :param x: str
    :param y: str
    :return: int
    """
    m = len(x)
    n = len(y)
    c = getCached(m, n)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                c[i][j] = c[i - 1][j - 1] + 1
            else:
                c[i][j] = max(c[i - 1][j], c[i][j - 1])
    return c[m][n]


def mergeImages(directory):
    items = os.listdir(directory)
    sorted_items = sorted(items)
    return sorted_items


if __name__ == '__main__':
    print(a)
    pass
