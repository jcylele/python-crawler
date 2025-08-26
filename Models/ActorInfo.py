
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
