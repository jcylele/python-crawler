# from Models.BaseModel import ActorModel
import Configs


class ActorInfo(object):
    actor_id: int
    actor_name: str
    actor_platform: str
    actor_link: str

    def __init__(self, actor=None):
        if actor is None:
            return
        self.actor_id = actor.actor_id
        self.actor_name = actor.actor_name
        self.actor_platform = actor.actor_platform
        self.actor_link = actor.actor_link

    def icon_file_name(self) -> str:
        return f"{self.actor_name}_{self.actor_platform}.png"

    def icon_file_path(self) -> str:
        return f"{Configs.formatIconFolderPath()}/{self.icon_file_name()}"

    def icon_ss_file_name(self) -> str:
        return f"{self.actor_name}_{self.actor_platform}(screenshot).png"

    def icon_ss_file_path(self) -> str:
        return f"{Configs.formatIconFolderPath()}/{self.icon_ss_file_name()}"

    def __repr__(self):
        return f"{self.actor_name} of {self.actor_platform}"