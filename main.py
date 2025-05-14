from Ctrls import DbCtrl, ManualCtrl, ActorCtrl, NoticeCtrl
from Download.DownloadTask import DownloadTask

if __name__ == '__main__':
    DownloadTask.initEnv()
    with DbCtrl.getSession() as session, session.begin():
        NoticeCtrl.regenerateCheckSums(session)
