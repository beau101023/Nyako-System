from typing import Type

from overrides import override

from LLM.nyako_llm import ConversationSession
from nyako.pipesys.MessageReciever import MessageReceiver
import params

from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from event_system.events.System import CommandEvent, CommandType
from pipesys import Pipe

class ConversationSessionProcessor(MessageReceiver):
    conversation_session: ConversationSession
    available_outputs: set[SystemOutputType]

    def __init__(self, listen_to):
        super().__init__(listen_to)

    @classmethod
    async def create(cls, listen_to: MessageEvent | Pipe | Type[MessageEvent]):
        self = ConversationSessionProcessor(listen_to)

        EventBusSingleton.subscribe(OutputAvailabilityEvent, self.onOutputStateUpdate)
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

    async def onOutputStateUpdate(self, event: OutputAvailabilityEvent):
        
        if not event.output_type in self.available_outputs and not event.output_available:
            return
        
        if(event.output_available):
            self.available_outputs.add(event.output_type)
        else:
            self.available_outputs.remove(event.output_type)

        self.conversation_session.updateSystemPrompt(self.getSystemPrompt())

    def getSystemPrompt(self):
        if(len(self.available_outputs) > 0):
            return params.nyako_prompt + " Available outputs: [" + "], [".join([output.name.lower() for output in self.available_outputs]) + "]"
        else:
            return params.nyako_prompt
        
    async def onStop(self, event: CommandEvent):
        if params.memorize_enabled:
            self.conversation_session.memorizeAll()