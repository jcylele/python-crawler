from Ctrls import DbCtrl, ResCtrl
from Download.DownloadTask import DownloadTask

if __name__ == '__main__':
    DownloadTask.initEnv()
    with DbCtrl.getSession() as session, session.begin():
        ret = ResCtrl.getResStatesOfActor(session, 2815)
        for res_state in ret:
            print(res_state)
