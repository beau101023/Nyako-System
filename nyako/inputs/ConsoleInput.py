import asyncio
from core.producer import Producer
from aioconsole import ainput

class ConsoleInput(Producer):
    def __init__(self):
        super().__init__()

    async def run(self):
        while True:
            message = await ainput(">>> ")
            await self.send(message)

    async def start(self):
        task = asyncio.create_task(self.run())
        return task