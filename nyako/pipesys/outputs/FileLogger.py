import os
import aiofiles
from datetime import datetime
from overrides import override
from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent, OutputMessageEvent, UserInputEvent
from event_system.events.System import CommandEvent, CommandType
from pipesys.Pipe import OutputPipe
from params import nyako_prompt

class FileLogger(OutputPipe):
    """
    Module that logs messages to a file.

    The file is named "logs/log<current date and time>.txt".

    The format of the log is:

    system: <system prompt>
    user: <message>
    assistant: <message>
    """

    def __init__(self):
        # Replace colons and spaces with underscores
        self.logfile_path = ("logs/log" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)

    @classmethod
    async def create(cls):
        self = FileLogger()

        EventBusSingleton.subscribe(UserInputEvent, self.onMessage)
        EventBusSingleton.subscribe(OutputMessageEvent, self.onMessage)

        async with aiofiles.open(self.logfile_path, mode='w') as logfile:
            await logfile.write(f"system: {nyako_prompt}\n")

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

        file_exists = os.path.exists(self.logfile_path)
        file_empty = file_exists and os.path.getsize(self.logfile_path) == 0

        async with aiofiles.open(self.logfile_path, mode='a') as logfile:
            # Add a newline between every message, without adding a newline at file start.
            if not file_empty:
                await logfile.write("\n")
            await logfile.write(f"{sender_name}: {str(event)}")