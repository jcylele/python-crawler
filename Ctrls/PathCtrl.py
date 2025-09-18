import os
import Configs
from Ctrls import RequestCtrl
from Models.ActorInfo import ActorInfo


def icon_file_name(actor_info: ActorInfo) -> str:
    return f"{actor_info.actor_name}_{actor_info.actor_platform}.png"


def icon_file_path(actor_info: ActorInfo) -> str:
    return f"{Configs.formatIconFolderPath()}/{icon_file_name(actor_info)}"


def smartActorIconSrc(actor_info: ActorInfo) -> str:
    # real icon
    file_path = icon_file_path(actor_info)
    if os.path.exists(file_path):
        return f"{Configs.FileWebPath}/{Configs.IconFolder}/{icon_file_name(actor_info)}"
    # remote url
    return RequestCtrl.formatActorIconUrl(actor_info)
