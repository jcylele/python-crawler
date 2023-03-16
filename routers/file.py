import http.server
import socketserver
import threading

import Configs

PORT = 1314


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=Configs.RootFolder, **kwargs)


# Create an object of the above class
handler_object = MyHttpRequestHandler


def create_server():
    with socketserver.TCPServer(("", PORT), handler_object) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()


def start():
    threading.Thread(target=create_server).start()
