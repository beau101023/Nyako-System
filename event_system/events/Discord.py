from dataclasses import dataclass
from typing import Union

from discord import (
    Client,
    DMChannel,
    GroupChannel,
    PartialMessageable,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
    VoiceClient,
)

from event_system import Event

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
