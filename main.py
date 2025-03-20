from Consts import NoticeType
from Ctrls import DbCtrl, ManualCtrl, ActorCtrl
from Download.DownloadTask import DownloadTask

if __name__ == '__main__':
    DownloadTask.initEnv()
    with DbCtrl.getSession() as session, session.begin():
        # ManualCtrl.namepattern(session)
        ActorCtrl.findAllSimilarActors(session)
