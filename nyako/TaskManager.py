import asyncio
from event_system.events.System import TaskCreatedEvent
from nyako.event_system.EventBus import EventBus
from nyako.event_system.EventBusSingleton import EventBusSingleton

class TaskManager:
    def __init__(self):
        self.tasks = []
        EventBusSingleton.get().subscribe(self.onTaskCreated, TaskCreatedEvent)

    def onTaskCreated(self, event: TaskCreatedEvent):
        print("Task registered for " + str(event.pretty_sender))
        self.tasks.append(event.task)

    async def run(self):
        await asyncio.gather(*self.tasks)