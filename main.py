from Consts import CacheKey
from Ctrls import DbCtrl, ManualCtrl, NoticeCtrl
from Download.DownloadTask import DownloadTask
from Utils import CacheUtil

if __name__ == '__main__':
    DownloadTask.initEnv()
    with DbCtrl.getSession() as session, session.begin():
        ManualCtrl.validateActor(session, 9082)
