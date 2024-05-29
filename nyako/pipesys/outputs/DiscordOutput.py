import discord
from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Discord import TextChannelConnectedEvent
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from pipesys import Pipe

class DiscordOutput:
    def __init__(self):
        self.sendChannel: discord.abc.MessageableChannel | None = None

    @classmethod
    async def create(cls, listen_to: Pipe):
        self = DiscordOutput()

        EventBusSingleton.subscribe(TextChannelConnectedEvent, self.set_channel)
        EventBusSingleton.subscribe(MessageEvent(sender=listen_to), self.send_message)

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD, True))
        return self

    def set_channel(self, event: TextChannelConnectedEvent):
        self.sendChannel = event.channel

    async def send_message(self, event: MessageEvent):
        # discord will throw an error if the message is empty
        if event.message is None or not event.message.strip():
            return

        if self.sendChannel is not None:
            await self.sendChannel.send(event.message)