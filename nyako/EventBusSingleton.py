from EventBus import EventBus

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