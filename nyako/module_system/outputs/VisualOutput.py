import openai
import tkinter as tk
import asyncio
import os
from PIL import Image, ImageTk

from module_system.core.listener import Listener
from params import API_KEY

openai.api_key = API_KEY

class VisualOutput(Listener):
    def __init__(self):
        super().__init__()
        self.window = tk.Tk()
        self.window.title("nyako")
        self.window.geometry("500x600")

        self.image_panel = tk.Label(self.window)
        self.image_panel.pack(side="top")

        self.text_panel = tk.Label(self.window, wraplength=500, justify="left", font=("Helvetica", 20))
        self.text_panel.pack(side="bottom")

        print(os.getcwd())

        self.setEmote("nyako/images/neutral.png")
        self.setText("[listening]")

    async def receive(self, message: str):
        emotion = await self.ChatGPTClassify(message)

        self.setText(message)
        self.setEmote("nyako/images/" + emotion + ".png")

    async def ChatGPTClassify(self, message: str):
        # emotion list: neutral,happy,wink,angry,disgust,surprised(positive),surprised(negative),sad,adoring,scared,inspired,questioning,confused,glitch,smug,exasperated,sleepy,asleep

        # Call the OpenAI API to classify the message
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that classifies messages into emotions or expressions. You reply with only one emotion or expression. Use ONLY the possible emotions. For example, 'crying' if the message contains sniffling, sobbing, etc. 'questioning' if the message is questioning someone. 'surprised(positive)' if the message contains positive surprise"},
                {"role": "user", "content": f"Possible emotions: neutral,happy,wink,crying,angry,disgust,surprised(positive),surprised(negative),sad,loving,adoring,scared,inspired,questioning,confused,glitch,smug,exasperated,asleep\nMessage: {message}"}],
            max_tokens=10,
            n=1,
            stop=None,
            temperature=0,
        )

        # Get the emotion from the response
        emotion = response['choices'][0]['message']['content']

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
        while True:
            self.window.update()
            await asyncio.sleep(0.1)

    async def getTask(self):
        return asyncio.create_task(self.updateWindowTask())