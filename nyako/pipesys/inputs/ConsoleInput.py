import asyncio
from aioconsole import ainput

from nyako.events.IO import UserInputEvent, SystemInputType
from events.System import TaskCreatedEvent
from nyako.event_system.EventBus import EventBus
from nyako.event_system.EventBusSingleton import EventBusSingleton

class ConsoleInput:
    event_bus: EventBus
    stopped: bool = False

    @classmethod
    async def create(cls):
        self = ConsoleInput()
        self.event_bus = EventBusSingleton.get()

        task = asyncio.create_task(self.run())
        await self.event_bus.publish(TaskCreatedEvent(task))
        return self

    async def run(self):
        while not self.stopped:
            message = await ainput(">>> ")
            await self.event_bus.publish(UserInputEvent(message, SystemInputType.CONSOLE))

    async def onStop(self):
        self.stopped = True