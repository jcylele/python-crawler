from fastapi import APIRouter
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from Utils import PathUtil

router = APIRouter()

assets_folder = PathUtil.formatStaticFile("assets")
templates = Jinja2Templates(directory=assets_folder)


@router.get("/", include_in_schema=False)
def vue(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
