import discord

from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Discord import BotReadyEvent, TextChannelConnectedEvent
from event_system.events.Pipeline import SystemInputType, UserInputEvent
from event_system.events.System import CommandEvent, CommandType
from pipesys import Pipe


class DiscordInput(Pipe):
    client: discord.Client

    def __init__(self):
        self.listeningChannel: discord.abc.MessageableChannel | None = None

    @classmethod
    async def create(cls):
        self = DiscordInput()

        # a part of the 'discord' package, separate from the event system which uses EventBus
        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.onStop)

        EventBusSingleton.subscribe(TextChannelConnectedEvent, self.onTextChannelConnect)

        EventBusSingleton.subscribe(BotReadyEvent, self.onBotReady)

        return self

    async def onTextChannelConnect(self, event: TextChannelConnectedEvent):
        self.listeningChannel = event.channel

    async def onBotReady(self, event: BotReadyEvent):
        self.client = event.client
        self.client.event(self.on_message)

    async def on_message(self, message: discord.Message):
        if not self.client.user:
            return

        if message.author.id == self.client.user.id:
            return

        if message.channel != self.listeningChannel:
            return

        inputEvent = UserInputEvent(
            message.content, self, SystemInputType.DISCORD, user_name=message.author.name
        )
        await EventBusSingleton.publish(inputEvent)

    async def onStop(self, event: CommandEvent):
        await self.client.close()
