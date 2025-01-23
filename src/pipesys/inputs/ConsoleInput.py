import asyncio
from aioconsole import ainput

from event_system.events.Pipeline import UserInputEvent, SystemInputType
from event_system.events.System import TaskCreatedEvent
from event_system import EventBus
from event_system import EventBusSingleton
from pipesys.Pipe import Pipe

class ConsoleInput(Pipe):
    event_bus: EventBus
    stopped: bool = False

    @classmethod
    async def create(cls):
        self = ConsoleInput()
        self.event_bus = EventBusSingleton.get()

        task = asyncio.create_task(self.run())
        await self.event_bus.publish(TaskCreatedEvent(task, "Console Input"))
        return self

    async def run(self):
        while not self.stopped:
            message = await ainput(">>> ")
            await self.event_bus.publish(UserInputEvent(message, self, SystemInputType.CONSOLE))

    async def onStop(self):
        self.stopped = True