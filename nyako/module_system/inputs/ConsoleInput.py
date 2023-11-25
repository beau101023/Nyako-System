import asyncio
from aioconsole import ainput

from EventTopics import Topics
from EventBus import EventBus

class ConsoleInput:
    event_bus: EventBus
    stopped: bool = False

    @classmethod
    async def create(cls, event_bus, publish_channel=Topics.Pipeline.USER_INPUT):
        self = ConsoleInput()
        self.event_bus = event_bus
        self.publish_channel = publish_channel

        self.task = asyncio.create_task(self.run())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
        return self

    async def run(self):
        while not self.stopped:
            message = await ainput(">>> ")
            await self.event_bus.publish(self.publish_channel, "[console] beau: " + message)

    async def onStop(self):
        self.stopped = True