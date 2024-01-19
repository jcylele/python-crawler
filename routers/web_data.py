from pydantic import BaseModel

from Models.BaseModel import ActorCategory


class ActorConditionForm(BaseModel):
    name: str
    category_list: list[int]
    tag_list: list[int]
    no_tag: bool
    min_score: int
    max_score: int

    # _actor_category_list: list[ActorCategory] = None

    def get_category_list(self):
        return list(map(ActorCategory, self.category_list))


class ActorTagForm(BaseModel):
    tag_name: str
    tag_priority: int


class DownloadLimitForm(BaseModel):
    actor_count: int
    post_count: int
    post_filter: int
    file_size: int
    allow_video: bool
    allow_img: bool
