from asyncio import Task
from dataclasses import dataclass
from enum import Enum

from event_system import Event, EventParameterFlag


class CommandType(Enum):
    """
    An enum representing the different commands recognized by the system.
    """

    STOP = 1
    LISTEN = 2
    SLEEP = 3
    WAKE = 4

    @staticmethod
    def from_string(str: str) -> "CommandType|None":
        return command_event_parse_dict.get(str, None)

    def to_string(self) -> str:
        for key, value in command_event_parse_dict.items():
            if self == value:
                return key

        return ""


"""
A dict mapping strings to CommandType enums.
Meant for parsing commands sent by an LLM.
Multiple strings map to the same command in case the LLM uses different words to refer to the same command.
"""
command_event_parse_dict = {
    "stop": CommandType.STOP,
    "shutdown": CommandType.STOP,
    "listen": CommandType.LISTEN,
    "listening": CommandType.LISTEN,
    "sleep": CommandType.SLEEP,
    "wake": CommandType.WAKE,
}


@dataclass
class CommandEvent(Event):
    """
    A dataclass representing a system-wide command to be executed.
    """

    command: CommandType | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED


class StartupStage(Enum):
    """
    An enum representing the different stages of the startup process.
    """

    BOOT = 1
    WARMUP = 2
    READY = 3


@dataclass
class StartupEvent(Event):
    """
    A dataclass representing an event to be raised when the system is starting up.
    """

    stage: StartupStage | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED


@dataclass
class TaskCreatedEvent(Event):
    """
    A dataclass representing an event to be broadcast when an asyncio task has been created, which will register that task with the task manager.

    Parameters:
    task (Task): the task that was created
    pretty_sender (str): a pretty string representation of the sender of the task
    """

    task: Task | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED
    pretty_sender: str | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED


@dataclass
class CommandAvailabilityEvent(Event):
    """
    A dataclass representing an event to be raised when the system's commands change availability.
    """

    command_type: CommandType | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED
    command_available: bool | EventParameterFlag | None = EventParameterFlag.NOT_SPECIFIED
