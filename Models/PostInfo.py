
class PostInfo(object):
    post_id: int
    is_dm: bool
    has_thumbnail: bool

    def __init__(self, post_id: int, is_dm: bool, has_thumbnail: bool):
        self.post_id = post_id
        self.is_dm = is_dm
        self.has_thumbnail = has_thumbnail