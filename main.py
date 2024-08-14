from Consts import WorkerType
from Ctrls import RequestCtrl, DbCtrl, ActorTagCtrl
from Workers.BaseFetchWorker import BaseFetchWorker

if __name__ == '__main__':
    # fetch_worker = BaseFetchWorker(WorkerType.FetchActors, None)
    # fetch_worker.driver.get("https://coomer.su/artists")
    # print(1)

    # requestSession = RequestCtrl.createRequestSession()
    # res = requestSession.head("https://coomer.su/onlyfans/user/lillybloomes")

    DbCtrl.init()
    with DbCtrl.getSession() as session, session.begin():
        for i in range(10):
            ret = ActorTagCtrl.getMinPriority(session, i)
            print(ret)

    pass
