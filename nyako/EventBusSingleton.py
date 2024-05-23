from EventBus import EventBus

from typing import Any, Callable

class EventBusSingleton(EventBus):
    """
    Singleton implementation of the EventBus.
    
    This class ensures that only one instance of EventBus exists and provides
    a static method to access that instance.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBusSingleton, cls).__new__(cls)
            cls._instance.__init__()  # Ensure the singleton is initialized
        return cls._instance

    @staticmethod
    def get():
        """
        Returns the singleton instance of the EventBusSingleton.
        
        Returns:
            EventBusSingleton: The singleton instance of the EventBusSingleton.
        """
        if EventBusSingleton._instance is None:
            EventBusSingleton._instance = EventBusSingleton()
        return EventBusSingleton._instance
    
    @staticmethod
    def subscribe(event: Any, handler: Callable[[Any], None]):
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
        EventBusSingleton.get().subscribe(event, handler)

    @staticmethod
    def unsubscribe(event: Any, handler: Callable[[Any], None]):
        """
        Unsubscribes a handler from a specific event type.
        
        Args:
            event (Any): Either an instance of a dataclass or a dataclass type representing
                         the event type to unsubscribe from.
            handler (Callable[[Any], None]): The handler to be removed from the list of subscribers.
        """
        EventBusSingleton.get().unsubscribe(event, handler)

    @staticmethod
    def publish(event: Any):
        """
        Publishes an event to all subscribers.
        
        Args:
            event (Any): An instance of a dataclass representing the event to publish.
        """
        EventBusSingleton.get().publish(event)