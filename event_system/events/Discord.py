from typing import Union

from dataclasses import dataclass
from discord import VoiceClient, Client

from event_system import Event

from discord import TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable, GroupChannel

PartialMessageableChannel = Union[
    TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable
]
MessageableChannel = Union[PartialMessageableChannel, GroupChannel]

@dataclass
class VoiceChannelConnectedEvent(Event):
    voice_client: VoiceClient

@dataclass
class VoiceChannelDisconnectedEvent(Event):
    pass

@dataclass
class TextChannelConnectedEvent(Event):
    channel: MessageableChannel

@dataclass
class BotReadyEvent(Event):
    client: Client