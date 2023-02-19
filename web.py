# web server for more convenient operations
# TODO far from completed, just for practice
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from Ctrls import DbCtrl
from routers import actor, actor_tag

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(actor.router)
app.include_router(actor_tag.router)

DbCtrl.init()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)