class Producer():
    def __init__(self):
        self.listener_methods = []

    async def link_to(self, listener_method):
        self.listener_methods.append(listener_method)

    async def unlink_to(self, listener_method):
        self.listener_methods.remove(listener_method)
        
    async def send(self, message: str):
        for listener_method in self.listener_methods:
            await listener_method(message)