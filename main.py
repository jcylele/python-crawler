from Ctrls import DbCtrl
from Models.BaseModel import ResModel

if __name__ == '__main__':
    DbCtrl.init()
    offset = 0
    limit = 10000
    while True:
        with DbCtrl.getSession() as session, session.begin():
            ret = session.query(ResModel).order_by(ResModel.res_id).offset(offset).limit(limit).all()
            if len(ret) == 0:
                break
            for res in ret:
                index = res.res_url.find("?")
                if index > 0:
                    res.res_url = res.res_url[:index]
            session.commit()
            offset += limit
            print(offset)
