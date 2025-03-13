import http.server
import socketserver
import threading

import Configs
from Utils import LogUtil


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=Configs.RootFolder, **kwargs)


# Create an object of the above class
handler_object = MyHttpRequestHandler


def create_server():
    with socketserver.TCPServer(("", Configs.FILE_PORT), handler_object) as httpd:
        LogUtil.info(f"file server listen at port {Configs.FILE_PORT}")
        httpd.serve_forever()


def start():
    threading.Thread(target=create_server).start()
