# from Models.BaseModel import ActorModel


class ActorInfo(object):
    actor_name: str
    actor_platform: str
    actor_link: str

    def __init__(self, actor=None):
        if actor is None:
            return
        self.actor_name = actor.actor_name
        self.actor_platform = actor.actor_platform
        self.actor_link = actor.actor_link
