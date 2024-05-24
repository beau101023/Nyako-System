from dataclasses import dataclass
from asyncio import Task
from enum import Enum

from Event import Event

from nyako.event_system.events.IO import SystemOutputType, SystemInputType

class CommandType(Enum):
    """
    An enum representing the different commands recognized by the system.
    """
    STOP = 1
    LISTEN = 2
    SLEEP = 3
    WAKE = 4

@dataclass
class CommandEvent(Event):
    """
    A dataclass representing a system-wide command to be executed.
    """
    command: CommandType

class StartupStageEnum(Enum):
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
    stage: StartupStageEnum

@dataclass
class TaskCreatedEvent(Event):
    """
    A dataclass representing an event to be broadcast when an asyncio task has been created, which will register that task with the task manager.

    Parameters:
    task (Task): the task that was created
    pretty_sender (str): a pretty string representation of the sender of the task
    """
    task: Task
    pretty_sender: str

@dataclass
class OutputAvailableUpdate(Event):
    """
    A dataclass representing an event to be raised when the system's outputs or commands change availability.
    """
    output_type: SystemOutputType
    output_available: bool

@dataclass
class InputActiveUpdate(Event):
    """
    A dataclass representing an event to be raised when the system's inputs change availability.
    """
    input_type: SystemInputType
    input_active: bool

@dataclass
class CommandAvailableUpdate(Event):
    """
    A dataclass representing an event to be raised when the system's commands change availability.
    """
    command: CommandType
    command_available: bool