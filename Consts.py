import random
from enum import Enum

import requests
from requests import Session

user_agents = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
    "MAC:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36",
    "Windows:Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36"
]

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    # "cache-control": "no-cache",
    "connection": "keep-alive",
    # "host": "coomer.party",
    # "pragma": "no-cache",
    "referer": "",
    "user-agent": ""
}

RootUrl = "https://coomer.party"
Platform = "onlyfans"
RootFolder = "D:/OnlyFans"
ActorsFileName = "actors.txt"
DbFileName = "record.db"

def createSession() -> Session:
    session = requests.Session()
    # cookie
    session.cookies = requests.cookies.RequestsCookieJar()
    # cookie.set("u", "6", domain="coomer.party", path="/")
    # header
    header = headers.copy()
    user_agent = random.choice(user_agents)  # 随机获取一个浏览器用户信息
    header['user-agent'] = user_agent
    session.headers = header

    return session


def formatActorsUrl(start_index: int) -> str:
    return f"{RootUrl}/artists?o={start_index}"


def formatUserUrl(actor_name: str, start_index: int) -> str:
    return f"{RootUrl}/{Platform}/user/{actor_name}?o={start_index}"


def formatPostUrl(actor_name: str, post_id: int) -> str:
    return f"{RootUrl}/{Platform}/user/{actor_name}/post/{post_id}"


def formatRecordPath(actor_name: str) -> str:
    return f"{RootFolder}/{actor_name}/{actor_name}.json"


def formatActorsPath() -> str:
    return f"{RootFolder}/{ActorsFileName}"


def formatActorFolderPath(actor_name: str) -> str:
    return f"{RootFolder}/{actor_name}"


def formatRecordPath() -> str:
    return f"{RootFolder}/{DbFileName}"


class WorkerType(Enum):
    FileDown = 1    # 资源文件保存
    PageDown = 2    # 网页拉取
    ResInfo = 3     # 资源信息获取

    AnalyseActors = 11  # 分析Actor列表
    AnalyseActor = 12   # 分析Actor的Post列表
    AnalysePost = 13    # 分析Post的资源列表

    ResValid = 21   # 下载文件验证



