from dataclasses import dataclass
from enum import Enum

from Event import Event

class AudioType(Enum):
    SYSTEM_IN = 1
    SYSTEM_OUT = 2
    DISCORD_OUT = 3
    DISCORD_IN = 4

@dataclass
class VolumeUpdatedEvent(Event):
    volume: float
    audio_type: AudioType

@dataclass
class SpeakingStateUpdate(Event):
    isSpeaking: bool
    audioType: AudioType