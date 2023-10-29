from abc import ABC, abstractmethod

class Listener(ABC):
    @abstractmethod
    async def receive(self, message: str):
        pass