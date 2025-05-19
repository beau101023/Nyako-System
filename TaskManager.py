import asyncio

from event_system import EventBusSingleton
from event_system.events.System import TaskCreatedEvent


class TaskManager:
    def __init__(self):
        self.tasks = []
        EventBusSingleton.subscribe(TaskCreatedEvent, self.on_task_created)

    def on_task_created(self, event: TaskCreatedEvent):
        if not isinstance(event.pretty_sender, str) or not isinstance(event.task, asyncio.Task):
            return
        
        print("Task registered for " + event.pretty_sender)
        self.tasks.append(event.task)

    async def run(self):
        await asyncio.gather(*self.tasks)

        print("All tasks gathered")
