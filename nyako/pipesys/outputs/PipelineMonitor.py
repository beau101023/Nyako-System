from overrides import override
from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from pipesys import OutputPipe, Pipe, MessageReceiver


class PipelineMonitor(MessageReceiver, OutputPipe):

    def __init__(self, listen_to):
        super().__init__(listen_to)

    @classmethod
    async def create(cls, listen_to: MessageEvent | Pipe | type[MessageEvent]):

        self = PipelineMonitor(listen_to)
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.CONSOLE, True))

        return self

    @override
    async def onMessage(self, event: MessageEvent):
        """
        Outputs a message to the console asynchonously.
        
        Parameters:
        message (str): the message to output
        """

        sender_name = event.sender.__class__.__name__

        print(f"{sender_name}: {str(event)}")