import time
import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from contextlib import asynccontextmanager

import Configs
from Consts import CacheKey, ErrorCode
from Models.Exceptions import BusinessException
from routers.schemas_others import UnifiedResponse
from routers import actor, actor_tag, download, others, vue, actor_group, chart, post, notice, favorite_folder, actor_tag_group
from Utils import CacheUtil, LogUtil, PyUtil
from Download import TaskManager, WebPool
from Download.DownloadTask import DownloadTask

# init browser env
Configs.initPlaywright()


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

# 注册业务异常处理器


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """处理业务逻辑异常，返回统一的错误响应格式"""

    LogUtil.warning(
        f"Business exception: {exc.error_code.name} - {exc.message}")

    # 返回 200 状态码，但响应体中包含 error_code
    # 这样前端可以统一处理，不需要检查 HTTP 状态码
    return JSONResponse(
        status_code=200,
        content=UnifiedResponse[None](
            error_code=exc.error_code,
            data=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未预期的系统异常"""
    LogUtil.error(f"Unhandled exception in {request.url.path}:")
    LogUtil.exception(exc)

    # 返回 500 错误，表示系统错误
    return JSONResponse(
        status_code=500,
        content={
            "error_code": ErrorCode.ServerError,
            "data": None,
            "error": "Internal server error"
        }
    )

# 耗时监控


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    if request.url.path.startswith("/api"):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        # response.headers["X-Process-Time"] = str(process_time)
        LogUtil.info(
            f"{request.method} {request.url.path} processed in {process_time:.2f}ms")
        return response
    else:
        return await call_next(request)

# 记录最后一次运行时间(特定操作的API)


@app.middleware("http")
async def monitor_last_run(request: Request, call_next):
    response = await call_next(request)

    # 仅当请求成功 (200 OK) 且是 API 请求时尝试记录
    # 具体的 "key是否存在" 判断逻辑在 tryUpdateLastRunTime 内部
    if response.status_code == 200 and request.url.path.startswith("/api/"):
        CacheUtil.tryUpdateLastRunTime(request.url.path)

    return response

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assets_folder = PyUtil.formatStaticFile("assets")
# html files
app.mount("/assets", StaticFiles(directory=assets_folder), name="assets")
# static files
app.mount(f"/{Configs.FileWebPath}",
          StaticFiles(directory=Configs.getRootFolder()), name="files")

app.include_router(actor.router)
app.include_router(actor_tag.router)
app.include_router(actor_group.router)
app.include_router(actor_tag_group.router)
app.include_router(favorite_folder.router)
app.include_router(chart.router)
app.include_router(download.router)
app.include_router(post.router)
app.include_router(notice.router)
app.include_router(others.router)
app.include_router(vue.router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Configs.getSetting(CacheKey.ServerPort)
    )
