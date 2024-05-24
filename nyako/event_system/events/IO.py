from enum import Enum
from dataclasses import dataclass

from nyako.event_system.events.Pipeline import MessageEvent, Pipe

class SystemInputType(Enum):
    """
    An enum representing all the possible sources of input.
    """
    CONSOLE = 1
    VOICE = 2
    DISCORD = 3
    DISCORD_VOICE = 4
    TWITCH = 5

class SystemOutputType(Enum):
    """
    An enum representing all the valid destinations for output.
    """
    CONSOLE = 1
    VOICE = 2
    DISCORD = 3
    DISCORD_VOICE = 4
    TWITCH = 5

class UserInputEvent(MessageEvent):
    """
    A class representing an event to be raised when the system receives input from a user.
    """
    message: str
    user_input_type: SystemInputType
    user_name: str = None
    priority: int = 3

    def __init__(self, message: str, user_input_type: SystemInputType, sender: Pipe, user_name: str = None, priority: int = 3):
        super.__init__(sender)
        self.message = message
        self.user_input_type = user_input_type
        self.user_name = user_name
        self.priority = priority

    def __str__(self) -> str:
        if self.user_name != None:
            strself = f"[{self.user_input_type.name.lower()}] {self.user_name}: {self.message}"
        else:
            strself = f"[{self.user_input_type.name.lower()}]: {self.message}"

        return strself

@dataclass
class Output(MessageEvent):
    """
    A dataclass representing an event to be raised to deliver output to a specific destination.
    """
    destination: SystemOutputType