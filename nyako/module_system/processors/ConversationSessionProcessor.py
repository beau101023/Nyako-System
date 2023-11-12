from LLM.nyako_llm import ConversationSession
import params
from EventTopics import Topics
from EventBus import EventBus

class ConversationSessionProcessor:
    conversation_session: ConversationSession
    tags: set[str]
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus):
        self = ConversationSessionProcessor()
        self.event_bus = event_bus
        self.event_bus.subscribe(self.onOutputStateUpdate, Topics.System.OUTPUT_STATE)
        
        # valid output tags
        self.tags = set()

        self.conversation_session = ConversationSession()
        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

        return self

    async def onMessage(self, message: str):
        # this blocks the event loop, but we want to pause processing until we get a response anyway
        response = self.conversation_session.query(message)
        await self.event_bus.publish(Topics.Pipeline.CONVERSATION_SESSION_REPLY, response)

    async def onOutputStateUpdate(self, outputStateUpdate: Topics.OutputStateUpdate):
        if(outputStateUpdate.output_active):
            self.tags.add(outputStateUpdate.tag.lower())
        else:
            self.tags.remove(outputStateUpdate.tag.lower())

        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

    def getSystemPrompt(self):
        if(len(self.tags) > 0):
            return params.nyako_prompt + " Available outputs: [" + "], [".join(self.tags) + "]"
        else:
            return params.nyako_prompt