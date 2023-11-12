import asyncio
from aioconsole import ainput

from EventTopics import Topics
from EventBus import EventBus

class ConsoleInput:
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus):
        self = ConsoleInput()
        self.event_bus = event_bus
        self.task = asyncio.create_task(self.run())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
        return self

    async def run(self):
        while True:
            message = await ainput(">>> ")
            await self.event_bus.publish(Topics.Pipeline.CONSOLE_IN, "[console] beau: " + message)