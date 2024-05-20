import asyncio
from Events import Events
from EventBus import EventBus
from EventBusSingleton import EventBusSingleton

class TaskManager:
    event_bus: EventBus

    def __init__(self):
        self.tasks = []
        EventBusSingleton.get().subscribe(self.onTaskCreated, Events.System.TaskCreated)

    def onTaskCreated(self, event: Events.System.TaskCreated):
        task = event.task
        
        print("Task registered for " + str(task))
        self.tasks.append(task)

    async def run(self):
        await asyncio.gather(*self.tasks)