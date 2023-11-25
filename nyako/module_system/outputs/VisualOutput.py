import tkinter as tk
import asyncio
import os
from PIL import Image, ImageTk
from EventTopics import Topics

from params import CLIENT_INSTANCE as client

class VisualOutput:
    stopped: bool = False

    def __init__(self, event_bus, listen_topic, master):
        self.event_bus = event_bus
        self.task = self.updateWindowTask()

        self.window = tk.Toplevel(master=master)
        self.window.title("nyako")
        self.window.geometry("500x600")

        self.image_panel = tk.Label(self.window)
        self.image_panel.pack(side="top")

        self.text_panel = tk.Label(self.window, wraplength=500, justify="left", font=("Helvetica", 20))
        self.text_panel.pack(side="bottom")

        print(os.getcwd())

        self.setEmote("nyako/images/neutral.png")
        self.setText("[listening]")

        self.event_bus.subscribe(self.onMessage, listen_topic)
        self.event_bus.subscribe(self.onStop, Topics.System.STOP)

    @classmethod
    async def create(cls, event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY, master=None):
        self = VisualOutput(event_bus, listen_topic, master)
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
        return self

    async def onMessage(self, message: str):
        if message == None or self.stopped:
            return

        emotion = await self.ChatGPTClassify(message)

        self.setText(message)
        self.setEmote("nyako/images/" + emotion + ".png")

    async def ChatGPTClassify(self, message: str):
        # Get the list of possible emotions from the names of the files in the /nyako/images directory
        possible_emotions = [os.path.splitext(filename)[0] for filename in os.listdir("nyako/images/")]

        # Call the OpenAI API to classify the message
        response = client.chat.completions.create(
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

        # debug
        print(emotion)

        return emotion
    
    def setEmote(self, path: str):
        img = Image.open(path)
        img.thumbnail((500, 500))
        img = ImageTk.PhotoImage(img)
        self.image_panel.configure(image=img)
        self.image_panel.image = img
        self.image_panel.pack(side="top", fill="both", expand="no")

    def setText(self, text: str):
        self.text_panel.configure(text=text)
        self.text_panel.pack(side="bottom", fill="x", expand="yes")

    async def updateWindowTask(self):
        while not self.stopped:
            self.window.update()
            await asyncio.sleep(0.1)

        try:
            self.window.destroy()
        except tk.TclError:
            pass

    async def onStop(self):
        self.stopped = True