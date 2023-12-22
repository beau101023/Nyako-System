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

        self.text_display = tk.Label(self.window, wraplength=500, justify="left", font=("Helvetica", 12))
        self.text_display.pack(side="top")

        self.stop_button = tk.Button(self.window, text="MANUAL STOP", command=self.publish_stop)
        self.stop_button.pack(side="bottom")

        self.sleep_enabled_button = tk.Button(self.window, text="SLEEP", command=self.toggle_sleep_enabled, background="red")
        self.sleep_enabled_button.pack(side="bottom")

        self.listening_enabled_button = tk.Button(self.window, text="LISTENING", command=self.toggle_listen_enabled, background="red")
        self.listening_enabled_button.pack(side="bottom")

        self.stop_enabled_button = tk.Button(self.window, text="STOP", command=self.toggle_stop_enabled, background="red")
        self.stop_enabled_button.pack(side="bottom")

        self.input_volume_slider = tk.Scale(self.window, from_=100, to=0, label="Input Volume")
        self.input_volume_slider.pack(side="left")

        self.output_volume_slider = tk.Scale(self.window, from_=100, to=0, label="Output Volume")
        self.output_volume_slider.pack(side="left")

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

    def publish_stop(self):
        # run from synchronous context
        asyncio.create_task(self.event_bus.publish(Topics.System.STOP))

    sleep_enabled: bool = False
    def toggle_sleep_enabled(self):
        self.sleep_enabled = not self.sleep_enabled
        event = Topics.OutputStateUpdate("sleep", self.sleep_enabled)
        asyncio.create_task(self.event_bus.publish(Topics.System.OUTPUT_STATE, event))
        if self.sleep_enabled:
            self.sleep_enabled_button.config(background="green")
        else:
            self.sleep_enabled_button.config(background="red")

    listen_enabled: bool = False
    def toggle_listen_enabled(self):
        self.listen_enabled = not self.listen_enabled
        event = Topics.OutputStateUpdate("listen", self.listen_enabled)
        asyncio.create_task(self.event_bus.publish(Topics.System.OUTPUT_STATE, event))
        if self.listen_enabled:
            self.listening_enabled_button.config(background="green")
        else:
            self.listening_enabled_button.config(background="red")

    stop_enabled: bool = False
    def toggle_stop_enabled(self):
        self.stop_enabled = not self.stop_enabled
        event = Topics.OutputStateUpdate("shutdown", self.stop_enabled)
        asyncio.create_task(self.event_bus.publish(Topics.System.OUTPUT_STATE, event))
        if self.stop_enabled:
            self.stop_enabled_button.config(background="green")
        else:
            self.stop_enabled_button.config(background="red")

    async def updateWindowTask(self):
        while not self.stopped:
            self.window.update()
            await self.update_sliders()
            await asyncio.sleep(0.015)

        self.window.destroy()

    previous_input_volume = None
    previous_output_volume = None
    async def update_sliders(self):
        # multiply by 0-1 instead of 0-100 AAAA my ears are bleeding
        input_volume = self.input_volume_slider.get() / 100
        output_volume = self.output_volume_slider.get() / 100

        if input_volume != self.previous_input_volume:
            event = Topics.VolumeUpdate(input_volume)
            await self.event_bus.publish(Topics.Audio.INPUT_VOLUME_UPDATE, event)
            self.previous_input_volume = input_volume

        if output_volume != self.previous_output_volume:
            event = Topics.VolumeUpdate(output_volume)
            await self.event_bus.publish(Topics.Audio.OUTPUT_VOLUME_UPDATE, event)
            self.previous_output_volume = output_volume

    async def onStop(self):
        self.stopped = True