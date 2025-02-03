import asyncio
import os

from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from event_system import EventBusSingleton
from event_system.events.System import CommandEvent, CommandType, TaskCreatedEvent
from event_system.events.Pipeline import MessageEvent
from pipesys import Pipe, MessageSource
from settings import ASYNCOPENAI as client

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

        self.setEmote("images/neutral.png")
        self.setText("[listening]")

        self.subscribe_to_message_sources(listen_to, self.onMessage)

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

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.onStop)

        task = asyncio.create_task(self.runVisualOutput())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Visual Output"))
        
        return self

    async def onMessage(self, event: MessageEvent):
        if event.message == None or self.stopped:
            return

        self.setText(event.message)

        emotion = await self.ChatGPTClassify(event.message)

        if emotion == None:
            self.setEmote("images/neutral.png")
            return
        self.setEmote("images/" + emotion + ".png")

    async def ChatGPTClassify(self, message: str):
        # Get the list of possible emotions from the names of the files in the /nyako/images directory
        possible_emotions = [os.path.splitext(filename)[0] for filename in os.listdir("images/")]

        # Call the OpenAI API to classify the message
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that classifies messages into emotions or expressions. You reply with only one emotion or expression. Use ONLY the given emotions. For example, 'crying' if the message contains sniffling, sobbing, etc. 'questioning' if the message is questioning someone. 'surprised(positive)' if the message contains positive surprise"},
                {"role": "user", "content": f"Possible emotions: {','.join(possible_emotions)}\nMessage: {message}"}],
            max_tokens=10,
            n=1,
            stop=None,
            temperature=0,
        )

        # Get the emotion from the response
        emotion = response.choices[0].message.content

        return emotion
    
    def setEmote(self, path: str):
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_panel.setPixmap(pixmap)

    def setText(self, text: str):
        self.text_panel.setText(text)

    async def runVisualOutput(self):
        self.window.show()

    async def onStop(self, event: CommandEvent):
        self.window.close()