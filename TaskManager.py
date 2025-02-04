import asyncio

from event_system import EventBusSingleton
from event_system.events.System import TaskCreatedEvent


class TaskManager:
    def __init__(self):
        self.tasks = []
        EventBusSingleton.subscribe(TaskCreatedEvent, self.onTaskCreated)

    def onTaskCreated(self, event: TaskCreatedEvent):
        print("Task registered for " + str(event.pretty_sender))
        self.tasks.append(event.task)

    async def run(self):
        await asyncio.gather(*self.tasks)

        print("All tasks gathered")
