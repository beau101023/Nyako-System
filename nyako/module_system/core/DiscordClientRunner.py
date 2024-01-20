import asyncio
import discord
import EventBus
from params import DISCORD_BOT_TOKEN
from EventTopics import Topics

class DiscordClientRunner:
    def __init__(self):
        self.client = discord.Client()

    @classmethod
    async def create(cls, event_bus: EventBus):
        self = DiscordClientRunner()

        self.task = asyncio.create_task(self.client.start(DISCORD_BOT_TOKEN))
        await event_bus.publish(Topics.System.TASK_CREATED, self.task)

        return self
    
    def getClient(self):
        return self.client