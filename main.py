import asyncio

from imagehash import ImageHash

from Consts import CacheKey
from Ctrls import (ActorFileCtrl, ActorSimilarCtrl, DbCtrl, ImageHashCtrl,
                   ManualCtrl, NoticeCtrl)
from Download import TaskManager
from Download.DownloadTask import DownloadTask
from Utils import CacheUtil, LogUtil, PyUtil


async def async_main():
    with DbCtrl.getSession() as session, session.begin():
        await ActorSimilarCtrl.check_similar_icons(session)
       # await ManualCtrl.testRedirect("https://n4.coomer.su/data/ef/95/ef95b882d0e0cfb5b6738d12362a00efa39e05dd4125022d388279f75b4c1a2d.mp4")


def main():
    # with DbCtrl.getSession() as session, session.begin():
    #     ManualCtrl.favorite_count_inversions(session)
    pass


if __name__ == '__main__':
    TaskManager.initEnv()
    # asyncio.run(async_main())
    main()
