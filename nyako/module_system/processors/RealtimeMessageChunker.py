import asyncio
from datetime import datetime, timedelta
from EventTopics import Topics
from EventBus import EventBus

from params import default_processor_delay
from params import default_no_input_interval_seconds

class RealtimeMessageChunker:
    event_bus: EventBus
    stopped: bool = False
    
    # gap_width_seconds is the amount of time to wait after the last message before processing the messages
    # no_input_interval_seconds is the amount of time to wait before sending a message indicating that there has been no input
    @classmethod
    async def create(cls, event_bus, processor_delay: int = default_processor_delay, no_input_interval_seconds: int = default_no_input_interval_seconds, listen_topic=Topics.Pipeline.USER_INPUT, send_topic=Topics.Pipeline.CHUNKER):
        self = RealtimeMessageChunker()
        self.event_bus = event_bus
        self.send_topic = send_topic
        
        self.task = asyncio.create_task(self.chunk_messages())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)

        self.sleeping = False
        self.paused = False

        self.event_bus.subscribe(self.onMessagePriority, listen_topic)
        self.event_bus.subscribe(self.onSleep, Topics.System.SLEEP)
        self.event_bus.subscribe(self.onWake, Topics.System.WAKE)
        self.event_bus.subscribe(self.onStop, Topics.System.STOP)
        self.event_bus.subscribe(self.onUserSpeakingStateUpdate, Topics.SpeechToText.USER_SPEAKING_STATE)

        # make sure the LLM gets error feedback
        self.event_bus.subscribe(self.onMessage, Topics.Router.ERROR)

        self.no_input_interval_seconds = no_input_interval_seconds
        self.processor_delay = processor_delay

        self.last_input_time = datetime.now()
        self.messages = []
        self.last_no_input_sent_time = datetime.now()

        return self

    async def chunk_messages(self):
        self.last_input_time = datetime.now()
        while not self.stopped:
            if self.sleeping or self.paused:
                await asyncio.sleep(1)
                continue

            if len(self.messages) > 0 and datetime.now() - self.last_input_time > timedelta(seconds=self.processor_delay):
                await self.process_messages()

                # delay the next chunk of messages by the processor delay
                self.last_input_time = datetime.now()

            elif len(self.messages) == 0 and datetime.now() - self.last_input_time > timedelta(seconds=self.no_input_interval_seconds):
                if datetime.now() >= self.last_no_input_sent_time + timedelta(seconds=self.no_input_interval_seconds):
                    time_since_last_input = str(datetime.now() - self.last_input_time).split(".")[0]

                    messages = "[no input ({0}s)]".format(time_since_last_input)

                    await self.send(messages)
                    self.last_no_input_sent_time = datetime.now()

            await asyncio.sleep(1)

        # send any remaining messages
        if len(self.messages) > 0:
            await self.process_messages()

    async def process_messages(self):
        messages_to_process = self.messages
        self.messages = []

        # join the messages into a string separated by newlines
        messages = "\n".join(messages_to_process)

        await self.send(messages)

    async def send(self, message: str):
        await self.event_bus.publish(self.send_topic, message)

    async def onMessage(self, message: str):
        if(self.sleeping):
            await self.event_bus.publish(Topics.System.WAKE)
        self.messages.append(message)

    async def onMessagePriority(self, message: str):
        self.last_input_time = datetime.now()
        await self.onMessage(message)

    async def onSleep(self):
        self.sleeping = True

    async def onWake(self):
        self.sleeping = False

    async def onStop(self):
        self.stopped = True

    async def onUserSpeakingStateUpdate(self, event: Topics.SpeakingStateUpdate):
        # if the user is speaking, pause the chunker
        # TODO: simplify the event object
        if event.starting:
            self.paused = True
        elif event.ending:
            self.paused = False
            self.last_input_time = datetime.now()