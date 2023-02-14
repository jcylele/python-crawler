# web server for more convenient operations
# TODO far from completed, just for practice

from enum import Enum
from typing import Union

from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from Entrance import MainOperation

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


class Item(BaseModel):
    name: str
    description: Union[str, None] = Field(default=None, title='The description of the item', max_length=20)
    price: float = Field(gt=0, description='The price must be greater than zero')
    tax: Union[float, None] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            }
        }


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "op_class": MainOperation})


@app.put("/items/{item_id}")
async def create_item(*, item_id: int, item: Item = Body(embed=True), priority: int = Body(example=10)):
    """

    :param priority:
    :param item_id:  path parameter
    :param item:  request body
    :return:
    """
    result = {"item_id": item_id, **item.dict()}
    result.update({"priority": priority})
    return result


@app.get("/users/{user_id}/items/{item_id}")
async def read_item(user_id: int = Path(title="owner id", ge=100),
                    item_id: str = Path(),
                    q: Union[str, None] = Query(default=..., regex='^[a-z]+$', deprecated=True, alias='item_q',
                                                title='title of q', description='desc of q'),
                    short: bool = False):
    item = {'item_id': item_id, "owner_id": user_id, "q": q}
    if not short:
        item.update({"desc": "This is an amazing item that has a long description"})
    return item


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return {"user_id": user_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]

# if __name__ == '__main__':
#     if True:
#         Entrance.enterOld()
#     else:
#         Entrance.enterUgly()
