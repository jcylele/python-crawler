import random
import socket
import socks
import requests
from requests import Session

from Models.ActorInfo import ActorInfo

__user_agents = [
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

__headers = {
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

__RootUrl = "https://coomer.su"


def initProxy():
    """
    set global proxy
    :return:
    """
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 10888)
    socket.socket = socks.socksocket


def createRequestSession() -> Session:
    """
    create a request session with cookies and user agent
    :return:
    """
    session = requests.Session()
    # cookie
    session.cookies = requests.cookies.RequestsCookieJar()
    # header
    header = __headers.copy()
    user_agent = random.choice(__user_agents)  # 随机获取一个浏览器用户信息
    header['user-agent'] = user_agent
    session.headers = header

    return session


def formatActorsUrl(start_index: int) -> str:
    return f"{__RootUrl}/artists#o={start_index}"


def formatActorIconUrl(actor_platform: str, actor_link: str) -> str:
    return f"{__RootUrl}/icons/{actor_platform}/{actor_link}"


def formatActorHref(actor_platform: str, actor_link: str) -> str:
    return f"{__RootUrl}/{actor_platform}/user/{actor_link}"


def formatActorUrl(actor_info: ActorInfo) -> str:
    return formatActorHref(actor_info.actor_platform, actor_info.actor_link)


def formatPostUrl(actor_info: ActorInfo, post_id: int) -> str:
    return f"{__RootUrl}/{actor_info.actor_platform}/user/{actor_info.actor_link}/post/{post_id}"


def formatFullUrl(relative_url: str) -> str:
    if relative_url.startswith('/'):
        return __RootUrl + relative_url
    else:
        return relative_url

