import os
import aiofiles
from datetime import datetime
from overrides import override
from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputMessageEvent, UserInputEvent
from nyako.pipesys.MessageReciever import MessageReceiver
from pipesys.Pipe import OutputPipe, Pipe
from params import nyako_prompt

class FileLogger(OutputPipe, MessageReceiver):
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

    def __init__(self, listen_to):
        super().__init__(listen_to)

        # Replace colons and spaces with underscores
        self.logfile_path = ("logs/log" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)

    @classmethod
    async def create(cls, listen_to: MessageEvent|Pipe|type[MessageEvent]):
        self = FileLogger(listen_to)

        EventBusSingleton.subscribe(UserInputEvent, self.onMessage)

        async with aiofiles.open(self.logfile_path, mode='w', encoding='utf-8') as logfile:
            await logfile.write(f"system: {nyako_prompt}")

        return self

    @override
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