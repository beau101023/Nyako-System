from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Pipeline import (
    MessageEvent,
    OutputAvailabilityEvent,
    OutputDeliveryEvent,
    SystemOutputType,
)
from pipesys import MessageSource, Pipe


class ConsoleOutput(Pipe):
    """
    Outputs messages to the console.
    """

    def __init__(self, listen_to: MessageSource):
        super().__init__()

        self.subscribe_to_message_sources(listen_to, self.onMessage)

    @classmethod
    async def create(cls, listen_to: MessageSource):
        """
        Creates an instance of the ConsoleOutput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        listen_to (str): the event or pipe to listen to for messages
        """

        self = ConsoleOutput(listen_to)
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.CONSOLE, True))

        return self

    async def onMessage(self, event: MessageEvent):
        """
        Outputs a message to the console asynchonously.

        Parameters:
        message (str): the message to output
        """

        print("\n" + str(event))
        await EventBusSingleton.publish(OutputDeliveryEvent(message=event.message, sender=self))
