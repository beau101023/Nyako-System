from dataclasses import dataclass
from enum import Enum
from typing import Type, TYPE_CHECKING

from event_system import Event

if TYPE_CHECKING:
    from pipesys import Pipe

@dataclass
class MessageEvent(Event):
    """
    An event that pipes raise when they have a message to pass along.
    """
    message: str|None = None
    sender: 'Pipe' | Type['Pipe'] | None = None

    def __str__(self) -> str:
        if self.message == None:
            return ""
        return self.message

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
    ALL = 0
    CONSOLE = 1
    VOICE = 2
    DISCORD = 3
    DISCORD_VOICE = 4
    TWITCH = 5

    @staticmethod
    def fromString(str: str) -> list['SystemOutputType'] | None:
        return system_output_parse_dict.get(str, None)
    
    def toString(self) -> str:
        for key, value in system_output_parse_dict.items():
            if self in value:
                return key

        return ""
    
"""
A dict mapping strings to SystemOutputType enums.
Meant for parsing an LLM's intended output, so multiple strings map to the same output type
    in case it uses different words to refer to the same output.
"""
system_output_parse_dict = {
    "voice": [SystemOutputType.VOICE],
    "discord_voice": [SystemOutputType.DISCORD_VOICE],
    "discord": [SystemOutputType.DISCORD],
    "console": [SystemOutputType.CONSOLE],
    "twitch": [SystemOutputType.TWITCH],
    "chat": [SystemOutputType.TWITCH]
}

@dataclass
class UserInputEvent(MessageEvent):
    """
    A class representing an event to be raised when the system receives input from a user.
    """
    message: str|None = None
    user_input_type: SystemInputType|None = None
    user_name: str|None = None
    priority: int = 0

    def __str__(self) -> str:
        if not self.message:
            return ""
        
        if not self.user_input_type and not self.user_name:
            return f"Untyped, anonymous message: {self.message}"
        
        if not self.user_input_type:
            return f"Untyped message by {self.user_name}: {self.message}"

        if not self.user_name:
            return f"[{self.user_input_type.name.lower()}]: {self.message}"

        return f"[{self.user_input_type.name.lower()}] {self.user_name}: {self.message}"

@dataclass
class OutputRoutingEvent(MessageEvent):
    """
    A dataclass representing an event to be raised to deliver output to a specific destination.
    """
    destination: SystemOutputType = SystemOutputType.CONSOLE
    
@dataclass
class OutputDeliveryEvent(MessageEvent):
    """
    A dataclass representing an event to be raised when an output is successfully delivered.
    """

@dataclass
class OutputAvailabilityEvent(Event):
    """
    A dataclass representing an event to be raised when the system's outputs or commands change availability.
    """
    output_type: SystemOutputType
    output_available: bool

@dataclass
class InputActivityEvent(Event):
    """
    A dataclass representing an event to be raised when the system's inputs change availability.
    """
    input_type: SystemInputType
    input_active: bool