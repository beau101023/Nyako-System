import asyncio

class EventBus:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, listener, event_type):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def unsubscribe(self, listener, event_type):
        if event_type in self._listeners:
            if listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)

    async def publish(self, event_type, *args):
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                if asyncio.iscoroutinefunction(listener):
                    await listener(*args)
                else:
                    listener(*args)