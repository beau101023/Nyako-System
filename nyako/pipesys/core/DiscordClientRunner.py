import asyncio
import discord
from params import DISCORD_BOT_TOKEN
from event_system.events.System import TaskCreatedEvent

from nyako.event_system.EventBusSingleton import EventBusSingleton

class DiscordClientRunner:
    def __init__(self):
        self.client = discord.Client()

    @classmethod
    async def create(cls) -> 'DiscordClientRunner':
        self = DiscordClientRunner()

        task = asyncio.create_task(self.client.start(DISCORD_BOT_TOKEN))
        await EventBusSingleton.publish(TaskCreatedEvent(task))

        return self
    
    def getClient(self):
        return self.client