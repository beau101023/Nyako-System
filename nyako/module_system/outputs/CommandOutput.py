from EventBus import EventBus
from EventTopics import Topics
import asyncio

class CommandOutput():
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus: EventBus):
        self = CommandOutput()
        self.sleep_length = 60*60 # 1 hour
        self.event_bus = event_bus
        self.event_bus.subscribe(self.onSleepingTriggered, Topics.Router.SLEEP)
        self.event_bus.subscribe(self.onWake, Topics.System.WAKE)
        self.event_bus.subscribe(self.onStopTriggered, Topics.Router.STOP)
        self.wake_event = asyncio.Event()
        return self
    
    async def setSleepingEnabled(self, enabled: bool):
        if enabled:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("sleep", True))
        else:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("sleep", False))

    async def setListeningEnabled(self, enabled: bool):
        if enabled:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("listen", True))
        else:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("listen", False))

    async def setStopEnabled(self, enabled: bool):
        if enabled:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("stop", True))
        else:
            await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("stop", False))

    async def onStopTriggered(self, text: str):
        await self.event_bus.publish(Topics.System.STOP)

    async def onSleepingTriggered(self, text: str):
        await self.event_bus.publish(Topics.System.SLEEP)

        _ = asyncio.create_task(self.wakeLaterTask())

    async def wakeLaterTask(self):
        # wakes after sleep_length seconds or when wake_event is set
        try:
            await asyncio.wait_for(self.wake_event.wait(), timeout=self.sleep_length)
        except asyncio.TimeoutError:
            # if the wake event isn't set, wake up
            await self.event_bus.publish(Topics.System.WAKE)
        finally:
            # if the wake event was set, Topics.System.WAKE was already published
            self.wake_event.clear()

    async def onWake(self):
        self.wake_event.set()
    
    async def onListeningTriggered(self, text: str):
        pass