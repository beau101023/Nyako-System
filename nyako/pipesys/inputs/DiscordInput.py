import discord
from nyako.event_system.EventBus import EventBus
from nyako.event_system.EventBusSingleton import EventBusSingleton

from nyako.events.IO import SystemInputType, UserInputEvent
from events.System import CommandEvent, CommandType, StartupStageEnum, StartupEvent
from events.System import StartupStageEnum

from events.Discord import TextChannelConnectedEvent

class DiscordInput:
    event_bus: EventBus
    client: discord.Client

    def __init__(self):
        self.listeningChannel: discord.TextChannel = None

    @classmethod
    async def create(cls, client: discord.Client):
        self = DiscordInput()
        self.event_bus = EventBusSingleton.get()
        self.client = client

        # a part of the 'discord' package, separate from the event system which uses EventBus
        client.event(self.onMessage)

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.onStop)
        EventBusSingleton.subscribe(StartupEvent(StartupStageEnum.WARMUP), self.onWarmup)

        return self

    async def onWarmup(self):
        if(self.listeningChannel == None):
            await EventBusSingleton.publish(CommandEvent(CommandType.SLEEP))

    async def onMessage(self, message: discord.Message):
        if message.author.id == self.client.user.id:
            return

        if(self.listeningChannel == None):
            self.listeningChannel = message.channel

            await EventBusSingleton.publish(TextChannelConnectedEvent(self.listeningChannel))

        if(message.channel != self.listeningChannel):
            return
        
        inputEvent = UserInputEvent(message.content, SystemInputType.DISCORD, user_name= message.author.name)
        await self.event_bus.publish(inputEvent)

    async def onStop(self):
        await self.client.close()