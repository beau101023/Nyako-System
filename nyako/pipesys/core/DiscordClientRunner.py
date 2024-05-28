import asyncio
import discord
from event_system.events.Discord import BotReadyEvent
from params import DISCORD_BOT_TOKEN
from event_system.events.System import TaskCreatedEvent

from event_system.EventBusSingleton import EventBusSingleton

class DiscordClientRunner:
    def __init__(self):

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.client.event(self.on_ready)

    @classmethod
    async def create(cls) -> 'DiscordClientRunner':
        self = DiscordClientRunner()

        task = asyncio.create_task(self.client.start(DISCORD_BOT_TOKEN))
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Discord Client"))

        return self
    
    async def on_ready(self):
        print("Discord Bot Connected")
        await EventBusSingleton.publish(BotReadyEvent(self.client))