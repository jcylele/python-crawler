
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

import Configs
# init browser env
Configs.initPlaywright()

from Download.DownloadTask import DownloadTask
from Download import TaskManager, WebPool
from Utils import LogUtil
from routers import actor, actor_tag, download, vue, actor_group, chart, post, notice, favorite_folder, actor_tag_group



DownloadTask.initEnv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 应用启动时 ---
    LogUtil.info("Application startup...")
    await WebPool.init_pool()

    yield

    LogUtil.info("Application shutdown...")
    # --- 应用关闭时 ---
    # await asyncio.to_thread(ActorFileCtrl.process_dirty_on_shutdown)
    await TaskManager.StopAllTasks()
    await WebPool.clear_pool()

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assets_folder = Configs.formatStaticFile("assets")
# html files
app.mount("/assets", StaticFiles(directory=assets_folder), name="assets")
# static files
app.mount(f"/{Configs.FileWebPath}",
          StaticFiles(directory=Configs.RootFolder), name="files")

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

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Configs.ServerPort
    )
