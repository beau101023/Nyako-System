import tkinter as tk
import asyncio
from EventTopics import Topics

class AdminEvents:
    stopped: bool = False

    def __init__(self, event_bus, listen_topic):
        self.event_bus = event_bus
        self.task = self.updateWindowTask()

        self.window = tk.Tk()
        self.window.title("Admin Events")
        self.window.geometry("500x600")

        self.text_display = tk.Label(self.window, wraplength=500, justify="left", font=("Helvetica", 20))
        self.text_display.pack(side="top")

        self.stop_button = tk.Button(self.window, text="STOP", command=self.stop_event)
        self.stop_button.pack(side="bottom")

        self.event_bus.subscribe(self.onMessage, listen_topic)
        self.event_bus.subscribe(self.onStop, Topics.System.STOP)

    @classmethod
    async def create(cls, event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY):
        self = AdminEvents(event_bus, listen_topic)
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
        return self

    async def onMessage(self, message: str):
        if message == None or self.stopped:
            return
        self.text_display.config(text=message)

    def stop_event(self):
        # run from synchronous context
        asyncio.create_task(self.event_bus.publish(Topics.System.STOP))

    async def updateWindowTask(self):
        while not self.stopped:
            self.window.update()
            await asyncio.sleep(0.1)

        self.window.destroy()

    async def onStop(self):
        self.stopped = True