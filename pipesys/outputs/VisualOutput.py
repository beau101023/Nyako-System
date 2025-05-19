import asyncio
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from event_system import EventBusSingleton
from event_system.events.Pipeline import MessageEvent
from event_system.events.System import CommandEvent, CommandType, TaskCreatedEvent
from pipesys import MessageSource, Pipe
from settings import ASYNCOPENAI as CLIENT


class VisualOutput(Pipe):
    """
    Provides a visual complement to other outputs.
    Current implementation is a simple window that displays emotion images based on sentiment analysis of the conversation.
    """

    stopped: bool = False

    def __init__(self, parent, listen_to: MessageSource):
        self.window = QMainWindow(parent)
        super().__init__()

        self.window.setWindowTitle("nyako")
        self.window.setGeometry(0, 0, 500, 600)

        widget = QWidget(self.window)
        self.window.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.image_panel = QLabel(self.window)
        layout.addWidget(self.image_panel, alignment=Qt.AlignmentFlag.AlignTop)

        self.text_panel = QLabel(self.window)
        self.text_panel.setWordWrap(True)
        layout.addWidget(self.text_panel, alignment=Qt.AlignmentFlag.AlignBottom)

        self.set_emote("images/neutral.png")
        self.set_text("[listening]")

        self.subscribe_to_message_sources(listen_to, self.on_message)

    @classmethod
    async def create(cls, listen_to: MessageSource, parent=None):
        """
        Creates an instance of the VisualOutput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        listen_topic (str): the channel to listen to for messages
        master (tk.Tk): the master window to use
        """
        self = VisualOutput(parent, listen_to)

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.on_stop)

        task = asyncio.create_task(self.run_visual_output())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Visual Output"))

        return self

    async def on_message(self, event: MessageEvent):
        if not isinstance(event.message, str) or self.stopped:
            return

        self.set_text(event.message)

        emotion = await self.chatgpt_classify(event.message)

        if emotion is None:
            self.set_emote("images/neutral.png")
            return
        self.set_emote("images/" + emotion + ".png")

    async def chatgpt_classify(self, message: str):
        # Get the list of possible emotions from the names of the files in the /nyako/images directory
        possible_emotions = [os.path.splitext(filename)[0] for filename in os.listdir("images/")]

        # Call the OpenAI API to classify the message
        response = await CLIENT.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that classifies messages into emotions or expressions. You reply with only one emotion or expression. Use ONLY the given emotions. For example, 'crying' if the message contains sniffling, sobbing, etc. 'questioning' if the message is questioning someone. 'surprised(positive)' if the message contains positive surprise",
                },
                {
                    "role": "user",
                    "content": f"Possible emotions: {','.join(possible_emotions)}\nMessage: {message}",
                },
            ],
            max_tokens=10,
            n=1,
            stop=None,
            temperature=0,
        )

        # Get the emotion from the response
        emotion = response.choices[0].message.content

        return emotion

    def set_emote(self, path: str):
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_panel.setPixmap(pixmap)

    def set_text(self, text: str):
        self.text_panel.setText(text)

    async def run_visual_output(self):
        self.window.show()

    async def on_stop(self, event: CommandEvent):
        self.window.close()
