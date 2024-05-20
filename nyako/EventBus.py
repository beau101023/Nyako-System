import asyncio
from dataclasses import fields, is_dataclass
from typing import Callable, Dict, List, Type, Any

class EventBus:
    """
    EventBus is a class that facilitates a publish-subscribe pattern for event handling.
    
    It allows subscribing handlers to specific dataclass events and publishing events to
    notify all relevant subscribers. The EventBus supports filtering of events based on
    dataclass field values.
    """

    def __init__(self):
        self._subscribers: Dict[Type, List[Callable[[Any], bool]]] = {}

    def subscribe(self, event: Any, handler: Callable[[Any], None]):
        """
        Subscribes a handler to a specific event type with optional filtering based on event fields.
        
        Args:
            event (Any): An instance of a dataclass or a dataclass type representing the event type to subscribe to.
                         In the case of an instance, the instance fields are used for filtering events.
            handler (Callable[[Any], None]): A callable that handles the event. It must accept a single
                                             argument, which is the event instance.
        
        Raises:
            TypeError: If filter_event is not a dataclass instance or type.
        """
        if not (is_dataclass(event) or (isinstance(event, type) and is_dataclass(event))):
            raise TypeError("filter_event must be a dataclass instance or dataclass type")
        
        event_class = event if isinstance(event, type) else type(event)
        if event_class not in self._subscribers:
            self._subscribers[event_class] = []
        filter_func = self._create_filter_func(event) if not isinstance(event, type) else lambda _: True
        self._subscribers[event_class].append((handler, filter_func))

    def unsubscribe(self, event: Any, handler: Callable[[Any], None]):
        """
        Unsubscribes a handler from a specific event type.
        
        Args:
            event (Any): Either an instance of a dataclass or a dataclass type representing
                         the event type to unsubscribe from.
            handler (Callable[[Any], None]): The handler to be removed from the list of subscribers.
        """

        event_class = event if isinstance(event, type) else type(event)

        if event_class in self._subscribers:
            self._subscribers[event_class] = [
                (h, f) for h, f in self._subscribers[event_class] if h != handler
            ]

    def _create_filter_func(self, filter_event: Any) -> Callable[[Any], bool]:
        """
        Creates a filter function for an event based on the provided filter_event dataclass instance.
        
        Args:
            filter_event (Any): An instance of a dataclass with fields used for filtering events.
        
        Returns:
            Callable[[Any], bool]: A function that takes an event and returns True if the event
                                   matches the filter criteria, otherwise False.
        """
        def filter_func(event: Any) -> bool:
            return all(getattr(event, field.name) == getattr(filter_event, field.name)
                       for field in fields(filter_event) if getattr(filter_event, field.name) is not None)
        return filter_func

    async def publish(self, event: Any):
        """
        Publishes an event to all subscribed handlers that match the event's type and filter criteria.
        
        Args:
            event (Any): An instance of a dataclass representing the event to be published.
        
        Example:
            await event_bus.publish(CustomEvent(channel=Channel.CONSOLE_INPUT, message="Hello", user_id=1))
        """
        event_class = type(event)
        if event_class in self._subscribers:
            for handler, filter_func in self._subscribers[event_class]:
                if filter_func(event):
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)