from LLM.nyako_llm import ConversationSession
from module_system.core.listener import Listener
from module_system.core.producer import Producer

class ConversationSessionProcessor(Producer, Listener):
    def __init__(self):
        super().__init__()
        self.conversation_session = ConversationSession()

    async def receive(self, message: str):
        # this blocks the event loop, but we want to pause processing until we get a response anyway
        response = self.conversation_session.query(message)
        await self.send(response)