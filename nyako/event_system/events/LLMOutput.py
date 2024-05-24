from dataclasses import dataclass

from Event import Event

@dataclass
class Error(Event):
    """
    A dataclass representing an event raised when the language model does not provide a valid tag for routing a message.

    Fields:
    message (string): the text associated with the erroneous output
    tag (string): the malformed tag text, if any
    """
    message: str
    tag: str = None