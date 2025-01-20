from LLM.nyako_llm import ConversationSession
from pipesys import Pipe, MessageSource
import params

from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, OutputDeliveryEvent, SystemOutputType
from event_system.events.System import CommandEvent, CommandType

class ConversationSessionProcessor(Pipe):
    conversation_session: ConversationSession
    available_outputs: set[SystemOutputType]
    buffer_size: int

    def __init__(self, listen_to: MessageSource | list[MessageSource], track_outputs_from: MessageSource, buffer_size=10):
        super().__init__()

        self.subscribeAll(listen_to, self.onMessage)
        self.subscribeAll(track_outputs_from, self.onOutputDelivered)

    @classmethod
    async def create(cls, listen_to: MessageEvent | Pipe | list[MessageSource], track_LLM_outputs_from: MessageSource = OutputDeliveryEvent, buffer_size=10):
        self = ConversationSessionProcessor(listen_to)

        EventBusSingleton.subscribe(OutputAvailabilityEvent, self.onOutputsChange)
        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.onStop)
        
        # valid output tags
        self.available_outputs = set()

        self.conversation_session = ConversationSession()
        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

        return self

    @override
    async def onMessage(self, event: MessageEvent):
        # this blocks the event loop, but we want to pause processing until we get a response anyway
        response = self.conversation_session.query(str(event))

        await EventBusSingleton.publish(MessageEvent(response, self))

        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

    async def onOutputDelivered(self, event: MessageEvent):
        if(event.message):
            await self.conversation_session.addLLMMessageToContext(event.message)

    async def onOutputsChange(self, event: OutputAvailabilityEvent):
        
        if not event.output_type in self.available_outputs and not event.output_available:
            return
        
        if(event.output_available):
            self.available_outputs.add(event.output_type)
        else:
            self.available_outputs.remove(event.output_type)

        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

    def getSystemPrompt(self):
        valid_tags = [output.toString() for output in self.available_outputs]

        if(len(self.available_outputs) > 0):
            return params.nyako_prompt + " Available outputs: [" + "], [".join(valid_tags) + "]"
        else:
            return params.nyako_prompt
        
    async def onStop(self, event: CommandEvent):
        if params.memorize_enabled:
            self.conversation_session.memorizeAll()