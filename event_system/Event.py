from abc import ABC
from enum import Enum


class Event(ABC):
    """
    Marker interface for events.
    """

    pass


class EventParameterFlag(Enum):
    NOT_SPECIFIED = "NOT_SPECIFIED"
