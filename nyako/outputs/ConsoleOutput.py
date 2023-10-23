import asyncio

from core.listener import Listener

class ConsoleOutput(Listener):
    def __init__(self):
        super().__init__()

    async def receive(self, message: str):
        print(message)