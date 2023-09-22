# web server for more convenient operations
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from Ctrls import RequestCtrl
from Download.DownloadTask import DownloadTask
from routers import actor, actor_tag, download, file, vue

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

app.include_router(actor.router)
app.include_router(actor_tag.router)
app.include_router(download.router)
app.include_router(vue.router)

# start file server
# TODO redirect from fastAPI
file.start()

DownloadTask.initEnv()

# RequestCtrl.initProxy()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
