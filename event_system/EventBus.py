import asyncio
from typing import Callable, Coroutine, Dict, List, Type, Any, Tuple, Union, TypeVar

from event_system import Event

AnyEvent = TypeVar('AnyEvent', bound=Event)
"""
AnyEvent is a TypeVar that is bound to the Event class.

We do this because, by default, using the Event class directly refers to only the Event class, not any subtypes.
"""

EventHandler = Union[Callable[[AnyEvent], None], Callable[[AnyEvent], Coroutine[Any,Any,None]]]

class EventBus:
    """
    EventBus is a class that facilitates a publish-subscribe pattern for event handling.
    
    It allows subscribing handlers to specific dataclass events and publishing events to
    notify all relevant subscribers. The EventBus supports filtering of events based on
    dataclass field values.
    """
    EventFilter = Callable[[AnyEvent], bool]
    Subscriber = Tuple[EventHandler, EventFilter]
    EventSubscriptions = Dict[Type[AnyEvent], List[Subscriber]]

    def __init__(self):
        self._subscribers: EventBus.EventSubscriptions = {}        
        """A dictionary that maps an event type to pairs of :class:`EventHandler` and :class:`EventFilter`.
            The :meth:`publish` method notifies subscribers from this dictionary by looking up the published event by type,
            checking the published event against all :class:`EventFilter` functions, and calling the corresponding :class:`EventHandler` functions."""

    def subscribe(self, event: Event|Type[Event], handler: EventHandler):
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

    def unsubscribe(self, event: Event|Type[Event], handler: EventHandler):
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

    def _create_filter_func(self, event_filter: Event) -> EventFilter:
        """
        Creates a filter function for the given event instance.

        The returned function checks:
          - If a field value in `event_filter` is None, it does not filter on that field.
          - If a field value is a type, the corresponding event's field must be an instance of that type.
          - Otherwise, the event's field must match the `event_filter` value exactly.

        Args:
            event_filter: An Event instance with field values used for filtering.

        Returns:
            A callable that takes an Event and returns True if it matches the filter criteria,
            and False otherwise.
        """
        def filter_func(event: Event) -> bool:
            for field_name, filter_value in vars(event_filter).items():
                # Skip fields explicitly set to None, meaning "ignore this field"
                if filter_value is None:
                    continue

                event_value = getattr(event, field_name, None)

                # If the filter_value is a type, ensure the event_value is an instance of that type
                if isinstance(filter_value, type):
                    if not isinstance(event_value, filter_value):
                        return False
                else:
                    # Otherwise, require an exact match
                    if event_value != filter_value:
                        return False

            return True

        return filter_func