import asyncio
from datetime import datetime, timedelta
from EventTopics import Topics

class RealtimeMessageChunker:
    # gap_width_seconds is the amount of time to wait after the last message before processing the messages
    # no_input_interval_seconds is the amount of time to wait before sending a message indicating that there has been no input
    @classmethod
    async def create(cls, event_bus, processor_delay: int = 5, no_input_interval_seconds: int = 30):
        self = RealtimeMessageChunker()
        self.event_bus = event_bus
        
        self.task = asyncio.create_task(self.chunk_messages())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)

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
        while True:
            if len(self.messages) > 0 and datetime.now() - self.last_input_time > timedelta(seconds=self.processor_delay):
                messages_to_process = self.messages
                self.messages = []

                # join the messages into a string separated by newlines
                messages = "\n".join(messages_to_process)

                await self.send(messages)

                # delay the next chunk of messages by the processor delay
                self.last_input_time = datetime.now()

            elif len(self.messages) == 0 and datetime.now() - self.last_input_time > timedelta(seconds=self.no_input_interval_seconds):
                if datetime.now() >= self.last_no_input_sent_time + timedelta(seconds=self.no_input_interval_seconds):
                    time_since_last_input = str(datetime.now() - self.last_input_time).split(".")[0]

                    messages = "[no input ({0}s)]".format(time_since_last_input)

                    await self.send(messages)
                    self.last_no_input_sent_time = datetime.now()

            await asyncio.sleep(1)

    async def send(self, message: str):
        await self.event_bus.publish(Topics.Pipeline.CHUNKER, message)

    async def onMessage(self, message: str):
        self.messages.append(message)

    async def priority_recieve(self, message: str):
        self.messages.append(message)
        self.last_input_time = datetime.now()