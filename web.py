# web server for more convenient operations
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

import Configs
from Download.DownloadTask import DownloadTask
from routers import actor, actor_tag, download, file, vue, actor_group, chart, post, notice, favorite_folder, actor_tag_group

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assets_folder = Configs.formatStaticFile("assets")
app.mount("/assets", StaticFiles(directory=assets_folder), name="assets")

app.include_router(actor.router)
app.include_router(actor_tag.router)
app.include_router(actor_group.router)
app.include_router(actor_tag_group.router)
app.include_router(favorite_folder.router)
app.include_router(chart.router)
app.include_router(download.router)
app.include_router(post.router)
app.include_router(notice.router)
app.include_router(vue.router)

# start file server
# TODO redirect from fastAPI
file.start()

DownloadTask.initEnv()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=7878
    )
