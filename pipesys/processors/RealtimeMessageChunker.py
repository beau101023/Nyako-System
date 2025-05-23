import asyncio
from datetime import datetime

from event_system import EventBusSingleton
from event_system.events.Audio import AudioDirection, SpeakingStateUpdate
from event_system.events.Pipeline import MessageEvent, UserInputEvent
from event_system.events.System import CommandEvent, CommandType, TaskCreatedEvent
from pipesys import MessageSource, Pipe
from settings import default_no_input_interval_seconds, default_processor_delay


class RealtimeMessageChunker(Pipe):
    no_input_interval_seconds: int
    processor_delay: float

    def __init__(self, listen_to: MessageSource):
        super().__init__()
        self.sleeping: bool = False
        self.paused: bool = False
        self.stopped: bool = False

        self.last_input_time: datetime = datetime.now()
        self.event_queue: list[UserInputEvent] = []
        self.last_no_input_sent_time: datetime = datetime.now()

        self.subscribe_to_message_sources(listen_to, self.on_message)

    # processor_delay is the amount of time to wait after the last message before processing the messages
    # no_input_interval_seconds is the amount of time to wait before sending a message indicating that there has been no input
    @classmethod
    async def create(
        cls,
        listen_to: MessageSource,
        processor_delay: float = default_processor_delay,
        no_input_interval_seconds: int = default_no_input_interval_seconds,
    ):
        self = RealtimeMessageChunker(listen_to)

        task = asyncio.create_task(self.chunk_messages())
        await EventBusSingleton.publish(TaskCreatedEvent(task, pretty_sender="Message Chunker"))

        EventBusSingleton.subscribe(CommandEvent(CommandType.SLEEP), self.on_sleep)
        EventBusSingleton.subscribe(CommandEvent(CommandType.WAKE), self.on_wake)
        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.on_stop)
        EventBusSingleton.subscribe(
            SpeakingStateUpdate(audio_direction=AudioDirection.INPUT),
            self.on_user_speaking_state_update,
        )

        self.no_input_interval_seconds = no_input_interval_seconds
        self.processor_delay = processor_delay

        return self

    async def chunk_messages(self):
        self.last_input_time = datetime.now()
        while not self.stopped:
            if self.sleeping or self.paused:
                await asyncio.sleep(0.1)
                continue

            if self.messages_queued() and self.user_inactivity_seconds() > self.processor_delay:
                await self.process_messages()

                # delay the next chunk of messages by the processor delay
                self.last_input_time = datetime.now()

            elif (
                not self.messages_queued()
                and self.user_inactivity_seconds() > self.no_input_interval_seconds
                and self.seconds_since_last_idle_response() > self.no_input_interval_seconds
            ):
                await self.send_no_input_message()

            await asyncio.sleep(0.1)

        # send any remaining messages
        if self.messages_queued():
            await self.process_messages()

    def seconds_since_last_idle_response(self) -> float:
        return (datetime.now() - self.last_no_input_sent_time).total_seconds()

    def user_inactivity_seconds(self) -> float:
        return (datetime.now() - self.last_input_time).total_seconds()

    async def send_no_input_message(self) -> None:
        time_since_last_input = str(datetime.now() - self.last_input_time).split(".")[0]

        messages = f"[no input ({time_since_last_input}s)]"

        self.last_no_input_sent_time = datetime.now()

        await self.send(messages)

    def messages_queued(self) -> bool:
        return len(self.event_queue) > 0

    async def process_messages(self) -> None:
        messages_to_process = [str(event) for event in self.event_queue]
        self.event_queue = []

        # join the messages into a string separated by newlines
        messages = "\n\n".join(messages_to_process)

        await self.send(messages)

    async def send(self, message: str):
        await EventBusSingleton.publish(MessageEvent(message, self))

    async def on_message(self, event: UserInputEvent):
        if not isinstance(event.priority, int):
            return

        # don't add if `event` has a lower priority than other queued events
        if self.queue_max_priority() > event.priority:
            return

        # past this point, we're actually queueing events, so wake up
        if self.sleeping:
            await EventBusSingleton.publish(CommandEvent(CommandType.WAKE))

        # if `event` has a higher priority than all queued events, clear queue and add
        if self.queue_max_priority() < event.priority:
            self.event_queue = []
            self.event_queue.append(event)
            return

        # event has the same priority, just add it
        self.event_queue.append(event)

    def queue_max_priority(self):
        if len(self.event_queue) == 0:
            return 0

        event_priorities: set[int] = set()

        for message in self.event_queue:
            if message.priority is None:
                event_priorities.add(-1)
            else:
                event_priorities.add(message.priority)

        return max(event_priorities)

    async def on_sleep(self, event: CommandEvent):
        self.sleeping = True

    async def on_wake(self, event: CommandEvent):
        self.sleeping = False

    async def on_stop(self, event: CommandEvent):
        self.stopped = True

    async def on_user_speaking_state_update(self, event: SpeakingStateUpdate):
        # if the user has finished a period of speech, update the last input time
        if not isinstance(event.is_speaking, bool):
            return

        if not event.is_speaking:
            self.last_input_time = datetime.now()

        # if the user is speaking, pause the chunker
        self.paused = event.is_speaking
