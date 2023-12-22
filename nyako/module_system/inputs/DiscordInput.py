import discord
from EventTopics import Topics
from EventBus import EventBus

from params import DISCORD_BOT_TOKEN

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
        self.event_bus.subscribe(self.on_warmup, Topics.System.WARMUP)

        await event_bus.publish(Topics.System.TASK_CREATED, self.start(DISCORD_BOT_TOKEN))

        return self

    # nyako will spam messages to herself but not have them sent if there's no active channel, so put her to sleep
    async def on_warmup(self):
        if(self.listeningChannel == None):
            await self.event_bus.publish(Topics.System.SLEEP)

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