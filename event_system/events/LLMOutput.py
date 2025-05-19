from dataclasses import dataclass

from event_system import Event, EventParameterFlag

from .Pipeline import SystemOutputType
from .System import CommandType


@dataclass
class NoTagsEvent(Event):
    """
    A dataclass representing an event raised when the language model does not provide any tags for routing a message.
    """

    pass


@dataclass
class InvalidTagEvent(Event):
    """
    A dataclass representing an event raised when the language model does not provide a valid tag for routing a message.

    Fields:
    message (string): the text associated with the erroneous output
    tag (string): the malformed tag text, or none if no tag was provided
    """

    tag: str | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED


@dataclass
class InactiveOutputEvent(Event):
    """
    A dataclass representing an event raised when the language model provides a valid tag, but that output is not available.

    Fields:
    message (string): the text associated with the erroneous output
    output_target (SystemOutputType): the target output that was unavailable
    """

    message: str | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
    tag: SystemOutputType | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED


@dataclass
class InactiveCommandEvent(Event):
    """
    A dataclass representing an event raised when the language model provides a valid command, but that command is not available.

    Fields:
    message (string): the text associated with the erroneous command
    command (CommandType): the command that was unavailable
    """

    command: CommandType | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
