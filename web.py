# web server for more convenient operations
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from Download.DownloadTask import DownloadTask
from routers import actor, actor_tag, download, file, vue, actor_group, chart, post

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
app.include_router(actor_group.router)
app.include_router(chart.router)
app.include_router(download.router)
app.include_router(post.router)
app.include_router(vue.router)

# start file server
# TODO redirect from fastAPI
file.start()

DownloadTask.initEnv()

# RequestCtrl.initProxy()
#
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    pass
