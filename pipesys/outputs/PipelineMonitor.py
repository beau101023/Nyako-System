from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from pipesys import Pipe, MessageSource


class PipelineMonitor(Pipe):

    def __init__(self, listen_to: MessageSource):
        super().__init__()

        self.subscribe_to_message_sources(listen_to, self.onMessage)

    @classmethod
    async def create(cls, listen_to: MessageSource):

        self = PipelineMonitor(listen_to)
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.CONSOLE, True))

        return self

    async def onMessage(self, event: MessageEvent):
        """
        Outputs a message to the console asynchonously.
        
        Parameters:
        message (str): the message to output
        """

        sender_name = event.sender.__class__.__name__

        try:
            print(f"{sender_name}: {str(event)}")
        except:
            print("[Unprintable message event.]")