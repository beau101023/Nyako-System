import os
import aiofiles
from datetime import datetime
from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, UserInputEvent
from pipesys import Pipe, MessageSource
from settings import chat_model_prompt

class FileLogger(Pipe):
    """
    Module that logs messages to a file.
    Automatically listens to all UserInputEvent.
    Additionally, listens to an additional event or pipe specified in the constructor.

    The file is named "logs/log<current date and time>.txt".

    The format of the log is:

    system: <system prompt>
    user: <message>
    assistant: <message>
    """

    def __init__(self, listen_to: MessageSource | list[MessageSource]):
        super().__init__()

        # Replace colons and spaces with underscores
        self.logfile_path = ("logs/log" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)

        self.subscribeAll(listen_to, self.onMessage)

    @classmethod
    async def create(cls, listen_to: MessageEvent|Pipe|type[MessageEvent]):
        self = FileLogger(listen_to)

        EventBusSingleton.subscribe(UserInputEvent, self.onMessage)

        async with aiofiles.open(self.logfile_path, mode='w', encoding='utf-8') as logfile:
            await logfile.write(f"system: {chat_model_prompt}")

        return self

    async def onMessage(self, event: MessageEvent):
        """
        Logs received messages to a file.

        Format:

        user: <message>
        assistant: <message>
        
        Parameters:
        message (str): the message to log
        """

        if isinstance(event, UserInputEvent):
            sender_name = "user"
        else:
            sender_name = "assistant"

        async with aiofiles.open(self.logfile_path, mode='a', encoding='utf-8') as logfile:
            # Add a newline between every message.
            await logfile.write(f"\n{sender_name}: {str(event)}")