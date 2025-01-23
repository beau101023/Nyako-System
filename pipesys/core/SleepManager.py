import asyncio

from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.System import CommandEvent, CommandType

# simple class to manage sleep/wake events
class SleepManager:
    wake_event: asyncio.Event

    @classmethod
    async def create(cls) -> 'SleepManager':
        self = SleepManager()
        self.wake_event = asyncio.Event()
        EventBusSingleton.subscribe(CommandEvent(CommandType.SLEEP), self.sleep)
        EventBusSingleton.subscribe(CommandEvent(CommandType.WAKE), self.wake)
        return self

    async def sleep(self, event: CommandEvent):
        await self.sleep_for(60*60) # 1 hour

    async def sleep_for(self, sleep_length: int):
        _ = asyncio.create_task(self.wakeLaterTask(sleep_length))

    async def wake(self, event: CommandEvent):
        self.wake_event.set()

    async def wakeLaterTask(self, sleep_length: int):
        # wakes after sleep_length seconds or when wake_event is set
        try:
            await asyncio.wait_for(self.wake_event.wait(), timeout=sleep_length)
        except asyncio.TimeoutError:
            # if the wake event isn't set, wake up
            await EventBusSingleton.publish(CommandEvent(CommandType.WAKE))
        finally:
            # if the wake event was set, Topics.System.WAKE was already published
            self.wake_event.clear()