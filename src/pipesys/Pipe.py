from abc import ABC
from typing import Union
from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent

MessageSource = Union[MessageEvent, 'Pipe', type[MessageEvent]]
class Pipe(ABC):
    """
    Marker interface for classes which take input and give output as part of a pipeline using EventBus.
    """
    def subscribeAll(self, listen_to: MessageSource | list[MessageSource], callback):
        if not isinstance(listen_to, list):
            listen_to = [listen_to]

        for source in listen_to:
            if isinstance(source, Pipe):
                event = MessageEvent(sender=source)
            else:
                event = source

            EventBusSingleton.subscribe(event, callback)