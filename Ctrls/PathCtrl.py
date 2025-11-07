import Configs
from Models.ModelInfos import ActorInfo


def icon_file_name(actor_info: ActorInfo) -> str:
    return f"{actor_info.actor_name}_{actor_info.actor_platform}.png"


def icon_file_path(actor_info: ActorInfo) -> str:
    return f"{Configs.formatIconFolderPath()}/{icon_file_name(actor_info)}"


def smartActorIconSrc(actor_info: ActorInfo) -> str:
    return f"{Configs.FileWebPath}/{Configs.IconFolder}/{icon_file_name(actor_info)}"
