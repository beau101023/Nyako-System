from dataclasses import dataclass
from enum import Enum

from event_system import Event, EventParameterFlag


class AudioType(Enum):
    SYSTEM = 1
    DISCORD = 2


class AudioDirection(Enum):
    INPUT = 1
    OUTPUT = 2


@dataclass
class VolumeUpdatedEvent(Event):
    volume: float | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
    audio_type: AudioType | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
    audio_direction: AudioDirection | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED


@dataclass
class SpeakingStateUpdate(Event):
    is_speaking: bool | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
    audio_type: AudioType | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
    audio_direction: AudioDirection | EventParameterFlag = EventParameterFlag.NOT_SPECIFIED
