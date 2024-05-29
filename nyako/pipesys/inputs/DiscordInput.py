import discord
from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Pipeline import SystemInputType, UserInputEvent
from event_system.events.System import CommandEvent, CommandType, StartupStage, StartupEvent
from event_system.events.System import StartupStage

from event_system.events.Discord import TextChannelConnectedEvent
from pipesys import Pipe

class DiscordInput(Pipe):
    client: discord.Client

    def __init__(self):
        self.listeningChannel: discord.abc.MessageableChannel | None = None

    @classmethod
    async def create(cls, client: discord.Client):
        self = DiscordInput()
        self.client = client

        # a part of the 'discord' package, separate from the event system which uses EventBus
        client.event(self.onMessage)

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.onStop)
        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.onWarmup)

        return self

    async def onWarmup(self, event: StartupEvent):
        if(self.listeningChannel == None):
            await EventBusSingleton.publish(CommandEvent(CommandType.SLEEP))

    async def onMessage(self, message: discord.Message):
        if self.client.user == None:
            return

        if message.author.id == self.client.user.id:
            return

        if(self.listeningChannel == None):
            self.listeningChannel = message.channel

            await EventBusSingleton.publish(TextChannelConnectedEvent(self.listeningChannel))

        if(message.channel != self.listeningChannel):
            return
        
        inputEvent = UserInputEvent(message.content, self, SystemInputType.DISCORD, user_name= message.author.name)
        await EventBusSingleton.publish(inputEvent)

    async def onStop(self, event: CommandEvent):
        await self.client.close()