import openai
import tkinter as tk
import asyncio
import os

from module_system.core.listener import Listener
from params import API_KEY

openai.api_key = API_KEY

class EmoteOutput(Listener):
    def __init__(self, image_panel: tk.Label):
        super().__init__()
        self.image_panel = image_panel

    async def receive(self, message: str):
        emotion = await self.ChatGPTClassify(message)

        # if the t.png image exists, use it
        if(os.path.exists("nyako/images/" + emotion + "t.png")):
            # talking image for 2 seconds, then normal image
            img_path = "nyako/images/" + emotion + "t.png"
            img = tk.PhotoImage(file=img_path)
            self.image_panel.configure(image=img)
            self.image_panel.image = img
            self.image_panel.pack(side="bottom", fill="both", expand="yes")

            # sleep for 2 seconds
            await asyncio.sleep(2)

            img_path = "nyako/images/" + emotion + ".png"
            img = tk.PhotoImage(file=img_path)
            self.image_panel.configure(image=img)
            self.image_panel.image = img
            self.image_panel.pack(side="bottom", fill="both", expand="yes")
        else:
            img_path = "nyako/images/" + emotion + ".png"
            img = tk.PhotoImage(file=img_path)
            self.image_panel.configure(image=img)
            self.image_panel.image = img
            self.image_panel.pack(side="bottom", fill="both", expand="yes")

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