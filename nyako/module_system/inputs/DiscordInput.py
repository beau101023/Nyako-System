import discord
from EventTopics import Topics
from EventBus import EventBus

class DiscordInput(discord.Client):
    event_bus: EventBus
    publish_channel: str

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    @classmethod
    async def create(cls, event_bus: EventBus, publish_channel=Topics.Pipeline.USER_INPUT):
        self = DiscordInput()
        self.event_bus = event_bus
        self.listeningChannel = None
        self.publish_channel = publish_channel

        self.event_bus.subscribe(self.onStop, Topics.System.STOP)

        return self

    async def on_message(self, message: discord.Message):

        # Make sure we won't be replying to ourselves.
        if message.author.id == self.user.id:
            return

        if(self.listeningChannel == None):
            self.listeningChannel = message.channel
            await self.event_bus.publish(Topics.Discord.LISTENING_CHANNEL_SET, self.listeningChannel)

        if(message.channel != self.listeningChannel):
            return

        await self.event_bus.publish(self.publish_channel, "[discord] " + message.author.name + ": " + message.content)

    async def onStop(self):
        await self.close()