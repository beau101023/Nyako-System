from dataclasses import dataclass
from typing import Type

from Event import Event

from pipesys.Pipe import Pipe

@dataclass
class MessageEvent(Event):
    """
    An event that pipes raise when they have a message to pass along.
    """
    message: str
    sender: Pipe | Type[Pipe]