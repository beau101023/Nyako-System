import asyncio
from EventBus import EventBus
from EventTopics import Topics

# simple class to manage sleep/wake events
class SleepManager:
    wake_event: asyncio.Event
    event_bus: EventBus

    def __init__(self):
        pass

    async def create(event_bus: EventBus):
        self = SleepManager()
        self.wake_event = asyncio.Event()
        self.event_bus = event_bus
        event_bus.subscribe(self.sleep, Topics.System.SLEEP)
        event_bus.subscribe(self.wake, Topics.System.WAKE)
        return self

    async def sleep(self):
        await self.sleep_for(60*60) # 1 hour

    async def sleep_for(self, sleep_length: int):
        _ = asyncio.create_task(self.wakeLaterTask(sleep_length))

    async def wake(self):
        self.wake_event.set()

    async def wakeLaterTask(self, sleep_length: int):
        # wakes after sleep_length seconds or when wake_event is set
        try:
            await asyncio.wait_for(self.wake_event.wait(), timeout=sleep_length)
        except asyncio.TimeoutError:
            # if the wake event isn't set, wake up
            await self.event_bus.publish(Topics.System.WAKE)
        finally:
            # if the wake event was set, Topics.System.WAKE was already published
            self.wake_event.clear()