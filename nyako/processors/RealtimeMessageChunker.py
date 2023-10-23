import asyncio
from datetime import datetime, timedelta
from core.listener import Listener
from core.producer import Producer

class RealtimeMessageChunker(Producer, Listener):
    # gap_width_seconds is the amount of time to wait after the last message before processing the messages
    # no_input_interval_seconds is the amount of time to wait before sending a message indicating that there has been no input
    def __init__(self, gap_width_seconds: int = 5, no_input_interval_seconds: int = 30):
        self.no_input_interval_seconds = no_input_interval_seconds
        self.gap_width_seconds = gap_width_seconds

        # have the reciever wait a bit before processing the first chunk of messages
        self.last_input_time = datetime.now()

        # messages that have been received
        self.messages = []

        # listeners to be called when messages are processed
        self.listeners = []

        # time when the last no input message was sent
        self.last_no_input_sent_time = datetime.now()

    async def chunk_messages(self):
        self.last_gap_time = datetime.now()
        self.last_input_time = datetime.now()
        while True:
            if len(self.messages) > 0 and datetime.now() - self.last_gap_time > timedelta(seconds=self.gap_width_seconds):
                messages_to_process = self.messages
                self.messages = []
                self.last_gap_time = datetime.now()

                # join the messages into a string separated by newlines
                messages = "\n".join(messages_to_process)

                await self.send(messages)

            elif len(self.messages) == 0 and datetime.now() - self.last_input_time > timedelta(seconds=self.no_input_interval_seconds):
                if datetime.now() >= self.last_no_input_sent_time + timedelta(seconds=self.no_input_interval_seconds):
                    time_since_last_input = str(datetime.now() - self.last_input_time).split(".")[0]

                    messages = "[no input ({0}s)]".format(time_since_last_input)

                    await self.send(messages)
                    self.last_no_input_sent_time = datetime.now()

            await asyncio.sleep(1)

    async def receive(self, message: str):
        self.messages.append(message)
        self.last_input_time = datetime.now()

    async def start(self):
        return asyncio.create_task(self.chunk_messages())