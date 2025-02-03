import discord
from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Discord import TextChannelConnectedEvent
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType, OutputDeliveryEvent
from pipesys import Pipe, MessageSource

class DiscordOutput(Pipe):
    def __init__(self, listen_to: MessageSource | list[MessageSource]):
        super().__init__()
        self.sendChannel: discord.abc.MessageableChannel | None = None

        self.subscribe_to_message_sources(listen_to, self.onMessage)

    @classmethod
    async def create(cls, listen_to: Pipe | MessageEvent | type[MessageEvent]):
        self = DiscordOutput(listen_to)

        EventBusSingleton.subscribe(TextChannelConnectedEvent, self.set_channel)

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD, True))
        return self

    def set_channel(self, event: TextChannelConnectedEvent):
        self.sendChannel = event.channel

    async def onMessage(self, event: MessageEvent):
        # discord will throw an error if the message is empty
        if event.message is None or not event.message.strip():
            return

        if self.sendChannel is not None:
            await self.sendChannel.send(event.message)
            await EventBusSingleton.publish(OutputDeliveryEvent(message=event.message, sender=self))