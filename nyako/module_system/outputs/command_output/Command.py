from enum import Enum

class Command(Enum):
    SLEEP = 1
    LISTEN = 2
    STOP = 3
    UNKNOWN = 4

    @classmethod
    def fromString(cls, text: str):
        if text == "sleep":
            return cls.SLEEP
        elif text == "listen":
            return cls.LISTEN
        elif text == "shutdown":
            return cls.STOP
        else:
            return cls.UNKNOWN

    def __str__(self):
        if self == Command.SLEEP:
            return "sleep"
        elif self == Command.LISTEN:
            return "listen"
        elif self == Command.STOP:
            return "shutdown"
        else:
            return "unknown"