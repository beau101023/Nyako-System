from dataclasses import dataclass
from enum import Enum

from event_system import Event


class AudioType(Enum):
    SYSTEM = 1
    DISCORD = 2


class AudioDirection(Enum):
    INPUT = 1
    OUTPUT = 2


@dataclass
class VolumeUpdatedEvent(Event):
    volume: float | None = None
    audio_type: AudioType | None = None
    audio_direction: AudioDirection | None = None


@dataclass
class SpeakingStateUpdate(Event):
    is_speaking: bool | None = None
    audio_type: AudioType | None = None
    audio_direction: AudioDirection | None = None
