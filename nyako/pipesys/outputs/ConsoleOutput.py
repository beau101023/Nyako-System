from overrides import override
from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from pipesys import OutputPipe, Pipe, MessageReceiver


class ConsoleOutput(MessageReceiver, OutputPipe):
    """
    Outputs messages to the console.
    """

    def __init__(self, listen_to):
        super().__init__(listen_to)

    @classmethod
    async def create(cls, listen_to: MessageEvent | Pipe | type[MessageEvent]):
        """
        Creates an instance of the ConsoleOutput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        listen_to (str): the event or pipe to listen to for messages
        """

        self = ConsoleOutput(listen_to)
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.CONSOLE, True))

        return self

    @override
    async def onMessage(self, event: MessageEvent):
        """
        Outputs a message to the console asynchonously.
        
        Parameters:
        message (str): the message to output
        """

        print("\n" + str(event))