from dataclasses import dataclass
import discord

from Event import Event

@dataclass
class VoiceChannelConnectedEvent(Event):
    client: discord.VoiceClient

@dataclass
class VoiceChannelDisconnectedEvent(Event):
    pass

@dataclass
class TextChannelConnectedEvent(Event):
    channel: discord.TextChannel