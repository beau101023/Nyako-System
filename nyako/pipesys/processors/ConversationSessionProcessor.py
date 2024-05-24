from LLM.nyako_llm import ConversationSession
import params
from EventBus import EventBus
from events.Event import Event

class ConversationSessionProcessor:
    conversation_session: ConversationSession
    tags: set[str]
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus, listen_to: Event):
        self = ConversationSessionProcessor()
        self.event_bus = event_bus
        self.event_bus.subscribe(self.onOutputStateUpdate, Topics.System.OUTPUT_STATE)
        self.event_bus.subscribe(self.onMessage, listen_topic)
        self.event_bus.subscribe(self.onStop, Topics.System.STOP)
        self.send_topic = send_topic
        
        # valid output tags
        self.tags = set()

        self.conversation_session = ConversationSession()
        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

        return self

    async def onMessage(self, message: str):
        # this blocks the event loop, but we want to pause processing until we get a response anyway
        response = self.conversation_session.query(message)

        await self.event_bus.publish(self.send_topic, response)

    async def onOutputStateUpdate(self, event: Topics.OutputStateUpdate):
        if not event.tag in self.tags and not event.output_active:
            return
        
        if(event.output_active):
            self.tags.add(event.tag.lower())
        else:
            self.tags.remove(event.tag.lower())

        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

    def getSystemPrompt(self):
        if(len(self.tags) > 0):
            return params.nyako_prompt + " Available outputs: [" + "], [".join(self.tags) + "]"
        else:
            return params.nyako_prompt
        
    async def onStop(self):
        self.conversation_session.memorizeAll()