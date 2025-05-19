import openai

import settings
from event_system import EventBusSingleton
from event_system.events.Pipeline import (
    MessageEvent,
    OutputAvailabilityEvent,
    OutputDeliveryEvent,
    SystemOutputType,
)
from event_system.events.System import CommandEvent, CommandType
from LLM.nyako_llm import ConversationSession
from pipesys import MessageSource, Pipe


class ConversationSessionProcessor(Pipe):
    conversation_session: ConversationSession
    available_outputs: set[SystemOutputType]
    buffer_size: int

    def __init__(
        self,
        listen_to: MessageSource | list[MessageSource],
        track_outputs_from: MessageSource,
        buffer_size=10,
    ):
        super().__init__()
        self.buffer_size = buffer_size

        self.subscribe_to_message_sources(listen_to, self.on_message)
        self.subscribe_to_message_sources(track_outputs_from, self.on_output_delivered)

    @classmethod
    async def create(
        cls,
        listen_to: MessageSource | list[MessageSource],
        track_llm_outputs_from: MessageSource = OutputDeliveryEvent,
        buffer_size=10,
    ):
        self = ConversationSessionProcessor(listen_to, track_llm_outputs_from, buffer_size)

        EventBusSingleton.subscribe(OutputAvailabilityEvent, self.on_outputs_change)
        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.on_stop)

        # valid output tags
        self.available_outputs = set()

        self.conversation_session = ConversationSession()
        self.conversation_session.update_system_prompt(self.get_system_prompt())

        return self

    async def on_message(self, event: MessageEvent):
        try:
            async for response_chunk in self.conversation_session.stream_query(
                str(event), self.buffer_size
            ):
                await EventBusSingleton.publish(MessageEvent(response_chunk, self))
        except openai.APIError as e:
            print(e.message)
        self.conversation_session.update_system_prompt(self.get_system_prompt())

    async def on_output_delivered(self, event: MessageEvent):
        if event.message:
            await self.conversation_session.add_llm_message_to_context(event.message)

    async def on_outputs_change(self, event: OutputAvailabilityEvent):
        if event.output_type not in self.available_outputs and not event.output_available:
            return

        if event.output_available:
            self.available_outputs.add(event.output_type)
        else:
            self.available_outputs.remove(event.output_type)

        self.conversation_session.update_system_prompt(self.get_system_prompt())

    def get_system_prompt(self):
        valid_tags = [output.to_string() for output in self.available_outputs]

        if len(self.available_outputs) > 0:
            return (
                settings.chat_model_prompt + " Available outputs: [" + "], [".join(valid_tags) + "]"
            )
        else:
            return settings.chat_model_prompt

    async def on_stop(self, event: CommandEvent):
        if settings.memorize_enabled:
            await self.conversation_session.memorize_all()
