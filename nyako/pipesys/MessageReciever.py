from abc import abstractmethod

from event_system import EventBusSingleton

from event_system.events.Pipeline import MessageEvent

from pipesys import Pipe

class MessageReceiver(Pipe):
    """
    Base class for a pipe that takes a MessageEvent or pipe and subscribes to an onMessage event.
    """

    def __init__(self, listen_to: MessageEvent|Pipe|type[MessageEvent]) -> None:
        super().__init__()

        if isinstance(listen_to, Pipe):
            event = MessageEvent(sender=listen_to)
        else:
            event = listen_to

        EventBusSingleton.subscribe(event, self.onMessage)

    @abstractmethod
    def onMessage(self, event: MessageEvent):
        pass