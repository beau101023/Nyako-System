import asyncio
from dataclasses import fields
from typing import Callable, Dict, List, Type, Any, Tuple

from event_system.Event import Event

class EventBus:
    """
    EventBus is a class that facilitates a publish-subscribe pattern for event handling.
    
    It allows subscribing handlers to specific dataclass events and publishing events to
    notify all relevant subscribers. The EventBus supports filtering of events based on
    dataclass field values.
    """

    def __init__(self):
        """
        Init function.

        Private fields:
        _subscribers (Dict[Type, List[Tuple[Callable[[Event], None], Callable[[Event], bool]]]):
            A dictionary that maps an event type to pairs of subscriber handlers and filter functions.
            These represent the handlers that are subscribed to the event type and the filter functions
            used to determine if an event should be passed to the handler.
        """
        self._subscribers: Dict[Type, List[Tuple[Callable[[Event], None], Callable[[Event], bool]]]] = {}

    def subscribe(self, event: Event|Type[Event], handler: Callable[[Event], None]):
        """
        Subscribes a handler to a specific event type with optional filtering based on event fields.
        
        Args:
            event: Either an Event instance or Type[Event] representing the event type to subscribe to.
                   In the case of an instance, the instance fields are used for filtering events.
            handler: A callable that handles the event. It must accept a single
                     argument, which is the event instance.
        
        Raises:
            TypeError: If event is not an instance of Event or a type inheriting from Event.
        """

        if not isinstance(event, Event) and not (isinstance(event, type) and issubclass(event, Event)):
            raise TypeError("The 'event' parameter must be an instance of an Event or a type inheriting from Event.")
        
        event_class = event if isinstance(event, type) else type(event)
        if event_class not in self._subscribers:
            self._subscribers[event_class] = []
        filter_func = self._create_filter_func(event) if not isinstance(event, type) else lambda _: True
        self._subscribers[event_class].append((handler, filter_func))

    def unsubscribe(self, event: Event|Type[Event], handler: Callable[[Event], None]):
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

    def _create_filter_func(self, filter: Event|Type[Event]) -> Callable[[Event], bool]:
        """
        Creates a filter function for an event based on the provided event instance or type.

        This filter function 
        
        Args:
            filter_event (Any): An instance of a dataclass with fields used for filtering events.
        
        Returns:
            Callable[[Any], bool]: A function that takes an event and returns True if the event
                                   matches the filter criteria, otherwise False.
        """
        def filter_func(event: Event) -> bool:
            return all(
                # if an event is passed like Event(arg=AType), filter should allow all events with `arg` of that type
                ( field.type == Type and isinstance(getattr(event, field.name), field.type) ) 
                # if an event is passed like Event(arg=1), filter should allow all events with `arg` of that value
                # alternatively, if the filter event has a 'None' argument, the filter will ignore that argument for filtering
                or getattr(event, field.name) == getattr(filter, field.name)
                    for field in fields(filter) if getattr(filter, field.name) is not None)
        return filter_func

    async def publish(self, event: Event):
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