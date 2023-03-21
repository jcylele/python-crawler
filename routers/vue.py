from fastapi import APIRouter
from starlette.requests import Request
from starlette.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="assets")


@router.get("/", include_in_schema=False)
def vue(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
