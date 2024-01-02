import discord
from EventTopics import Topics
from EventBus import EventBus

class DiscordInput:
    event_bus: EventBus
    publish_channel: str
    client: discord.Client

    def __init__(self):
        pass

    @classmethod
    async def create(cls, event_bus: EventBus, client: discord.Client, publish_channel=Topics.Pipeline.USER_INPUT):
        self = DiscordInput()
        self.event_bus = event_bus
        self.listeningChannel = None
        self.publish_channel = publish_channel
        self.client = client

        self.event_bus.subscribe(self.onStop, Topics.System.STOP)
        self.event_bus.subscribe(self.onWarmup, Topics.System.WARMUP)

        return self

    async def onWarmup(self):
        if(self.listeningChannel == None):
            await self.event_bus.publish(Topics.System.SLEEP)

    @client.event
    async def onMessage(self, message: discord.Message):

        if message.author.id == self.client.user.id:
            return

        if(self.listeningChannel == None):
            self.listeningChannel = message.channel
            await self.event_bus.publish(Topics.Discord.LISTENING_CHANNEL_SET, self.listeningChannel)

        if(message.channel != self.listeningChannel):
            return

        await self.event_bus.publish(self.publish_channel, "[discord] " + message.author.name + ": " + message.content)

    async def onStop(self):
        await self.client.close()