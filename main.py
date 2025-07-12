from Ctrls import DbCtrl, ManualCtrl, NoticeCtrl
from Download.DownloadTask import DownloadTask

if __name__ == '__main__':
    # width, height, duration = ActorFileCtrl.get_media_info("D:\\OnlyFans\\missreinat_9883\\720564715_1.mp4")
    DownloadTask.initEnv()
    with DbCtrl.getSession() as session, session.begin():
        NoticeCtrl.regenerateCheckSums(session)
