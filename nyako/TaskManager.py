import asyncio
from EventTopics import Topics
from EventBus import EventBus

class TaskManager:
    event_bus: EventBus

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.tasks = []
        self.event_bus.subscribe(self.onTaskCreated, Topics.System.TASK_CREATED)

    def onTaskCreated(self, task):
        self.tasks.append(task)

    async def run(self):
        await asyncio.gather(*self.tasks)