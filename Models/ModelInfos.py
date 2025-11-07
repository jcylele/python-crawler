"""
simplified info classes for models
"""


from Configs import DB_STR_LEN_LONG, DM_LEN_SINGLE_ID


class ActorInfo(object):
    """
    basic actor info, also as interface for ActorModel and ActorResponse
    """
    actor_id: int
    actor_name: str
    actor_platform: str
    actor_link: str

    def __init__(self, actor: "ActorModel" = None):
        if actor is None:
            return
        self.actor_id = actor.actor_id
        self.actor_name = actor.actor_name
        self.actor_platform = actor.actor_platform
        self.actor_link = actor.actor_link

    def __repr__(self):
        return f"{self.actor_name} of {self.actor_platform}"


class PostInfo(object):
    post_id: int
    post_id_str: str
    has_thumbnail: bool

    def __init__(self, post_id: int, post_id_str: str, has_thumbnail: bool):
        self.post_id = post_id
        self.post_id_str = post_id_str
        self.has_thumbnail = has_thumbnail

    @staticmethod
    def parsePostId(id_str: str) -> int:
        """
        从post id字符串中解析出post id， 失败时返回0， 成功时返回post id
        """
        is_dm = id_str.startswith('DM')
        if is_dm:
            id_len = len(id_str)
            if id_len > DB_STR_LEN_LONG: # DB varchar长度限制 目前未发现更长的
                return 0
            if id_len % DM_LEN_SINGLE_ID != 2: # DM开头，长度为2 + N * DM_LEN_SINGLE_ID
                return 0
            id_str = id_str[2:2 + DM_LEN_SINGLE_ID] # 取第一个id作为post_id, 实测无重复
        try:
            post_id = int(id_str)
        except Exception:
            return 0
        return post_id
