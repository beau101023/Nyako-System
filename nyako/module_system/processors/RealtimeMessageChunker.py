import asyncio
from datetime import datetime, timedelta
from module_system.core.listener import Listener
from module_system.core.producer import Producer

class RealtimeMessageChunker(Producer, Listener):
    # gap_width_seconds is the amount of time to wait after the last message before processing the messages
    # no_input_interval_seconds is the amount of time to wait before sending a message indicating that there has been no input
    def __init__(self, processor_delay: int = 5, no_input_interval_seconds: int = 30):
        super().__init__()
        self.no_input_interval_seconds = no_input_interval_seconds
        self.processor_delay = processor_delay

        # have the reciever wait a bit before processing the first chunk of messages
        self.last_input_time = datetime.now()

        # messages that have been received
        self.messages = []

        # time when the last no input message was sent
        self.last_no_input_sent_time = datetime.now()

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

    async def receive(self, message: str):
        self.messages.append(message)

    async def priority_recieve(self, message: str):
        self.messages.append(message)
        self.last_input_time = datetime.now()

    async def getTask(self):
        return asyncio.create_task(self.chunk_messages())