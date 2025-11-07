import asyncio
from Consts import CacheKey
from Ctrls import DbCtrl, ManualCtrl, NoticeCtrl
from Download.DownloadTask import DownloadTask
from Utils import CacheUtil


async def async_main():
    with DbCtrl.getSession() as session, session.begin():
        await ManualCtrl.testRedirect("https://n4.coomer.su/data/ef/95/ef95b882d0e0cfb5b6738d12362a00efa39e05dd4125022d388279f75b4c1a2d.mp4")


def main():
    with DbCtrl.getSession() as session, session.begin():
        ManualCtrl.fixNotice(session)


if __name__ == '__main__':
    DownloadTask.initEnv()
    # asyncio.run(async_main())
    main()
