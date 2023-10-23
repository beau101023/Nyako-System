class Producer():
    def __init__(self):
        self.listeners = []

    async def add_listener(self, listener):
        self.listeners.append(listener)

    async def remove_listener(self, listener):
        self.listeners.remove(listener)

    async def send(self, message: str):
        for listener in self.listeners:
            await listener.receive(message)