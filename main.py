import asyncio
from Consts import CacheKey
from Ctrls import DbCtrl, ManualCtrl, NoticeCtrl
from Download.DownloadTask import DownloadTask
from Utils import CacheUtil


async def async_main():
    with DbCtrl.getSession() as session, session.begin():
        await ManualCtrl.check_size(session, r"D:\OnlyFans\_downloading\gothscumbag_32004825_3.m4v", 3196801)


def main():
    with DbCtrl.getSession() as session, session.begin():
        ManualCtrl.removeActorFolders(session)


if __name__ == '__main__':
    DownloadTask.initEnv()
    # asyncio.run(async_main())
    main()
