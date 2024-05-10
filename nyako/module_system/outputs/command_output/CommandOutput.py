from EventBus import EventBus
from EventTopics import Topics
import asyncio

import Command as Command

class CommandOutput():

    """
    Accepts textless commands from the LLM.

    TODO: make the command syntax more distinct and understandable. LLM seems to have a hard time differentiating between commands and output tags.

    current commands:
        - [sleep] - puts the system to sleep for one hour, during which it can be woken by any input but will not produce idle messages
        - [listen] - does nothing. Allows the LLM to wait for further input.
        - [shutdown] - stops the system.
    """

    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus: EventBus):
        """
        Creates an instance of the CommandOutput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        """

        self = CommandOutput()
        self.sleep_length = 60*60 # 1 hour
        self.event_bus = event_bus
        self.event_bus.subscribe(self.onSleepingTriggered, Topics.Router.SLEEP)
        self.event_bus.subscribe(self.onStopTriggered, Topics.Router.SHUTDOWN)
        self.wake_event = asyncio.Event()
        return self
    
    async def setCommandEnabled(self, command: Command, enabled: bool):
        """
        Sets the enabled state of a command.

        Parameters:
        command (Command): the command to set the state of
        enabled (bool): whether the command should be enabled
        """

        await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate(str(command), enabled))

    async def onStopTriggered(self, text: str):
        await self.event_bus.publish(Topics.System.STOP)

    async def onSleepingTriggered(self, text: str):
        await self.event_bus.publish(Topics.System.SLEEP)
    
    async def onListeningTriggered(self, text: str):
        pass