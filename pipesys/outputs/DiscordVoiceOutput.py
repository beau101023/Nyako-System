import asyncio
from io import BytesIO

import discord
from pydub import AudioSegment

from event_system.EventBusSingleton import EventBusSingleton
from event_system.events.Audio import AudioDirection, AudioType, SpeakingStateUpdate
from event_system.events.Discord import VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent
from event_system.events.Pipeline import (
    MessageEvent,
    OutputAvailabilityEvent,
    OutputDeliveryEvent,
    SystemOutputType,
)
from event_system.events.System import StartupEvent, StartupStage, TaskCreatedEvent
from pipesys.Pipe import MessageSource, Pipe
from TTS import SileroTTS, TextToSpeech


class DiscordVoiceOutput(Pipe):
    """
    Module that recieves text input from a pipe, converts it to speech, and plays it on the discord voice channel the bot is currently connected to.
    """

    text_to_speech: TextToSpeech
    voice_connection: discord.VoiceClient | None = None

    def __init__(self):
        self.audio_queue = asyncio.Queue()
        self.voice_connection = None
        self.asyncio_main_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    @classmethod
    async def create(cls, listen_to: MessageSource, text_to_speech: TextToSpeech = SileroTTS()):
        self = DiscordVoiceOutput()

        self.text_to_speech = text_to_speech

        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.on_warmup)
        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.on_voice_channel_connected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.on_voice_channel_disconnected)
        self.subscribe_to_message_sources(listen_to, self.handle_message)

        EventBusSingleton.subscribe(
            SpeakingStateUpdate(audio_direction=AudioDirection.INPUT),
            self.on_user_speaking_state_change,
        )
        task = asyncio.create_task(self.playback_loop())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Voice Output Playback"))

        return self

    def on_warmup(self, event: StartupEvent):
        self.text_to_speech.warmup()

    async def on_voice_channel_connected(self, event: VoiceChannelConnectedEvent):
        if(not isinstance(event.voice_client, discord.VoiceClient)):
            return
        
        self.voice_connection = event.voice_client

        await EventBusSingleton.publish(
            OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, True)
        )

    async def on_voice_channel_disconnected(self, event: VoiceChannelDisconnectedEvent):
        self.voice_connection = None

        await EventBusSingleton.publish(
            OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, False)
        )

    async def on_user_speaking_state_change(self, event: SpeakingStateUpdate):
        # when user starts speaking, call the interrupt method
        if isinstance(event.is_speaking, bool) and event.is_speaking:
            await self.interrupt_speech()

    async def interrupt_speech(self):
        if self.voice_connection and self.voice_connection.is_playing():
            self.voice_connection.stop()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

    async def handle_message(self, event: MessageEvent):
        if not self.voice_connection or not isinstance(event.message, str):
            return

        # Generate audio in parallel
        audio_segment = self.text_to_speech.generate_speech(event.message)
        if audio_segment is None:
            return

        audio_data = self.convert_for_output(audio_segment).raw_data
        if not isinstance(audio_data, bytes):
            return

        # Enqueue
        await self.audio_queue.put((audio_data, event.message))

    async def playback_loop(self):
        while True:
            audio_data, message = await self.audio_queue.get()
            # Wait while voice is busy
            while self.voice_connection and self.voice_connection.is_playing():
                await asyncio.sleep(0.1)

            if not self.voice_connection:
                continue

            buffer = BytesIO(audio_data)
            self.voice_connection.play(
                discord.PCMAudio(buffer),
                after=lambda e: self.finished_playing_callback(e, message),
                wait_finish=False,
            )

    def convert_for_output(self, audio_segment: AudioSegment) -> AudioSegment:
        return audio_segment.set_channels(2).set_frame_rate(48000).set_sample_width(2)

    def finished_playing_callback(self, ex: Exception | None, message: str):
        asyncio.run_coroutine_threadsafe(
            EventBusSingleton.publish(
                SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.OUTPUT)
            ),
            self.asyncio_main_loop,
        )
        if ex is None:
            asyncio.run_coroutine_threadsafe(
                EventBusSingleton.publish(OutputDeliveryEvent(message=message)),
                self.asyncio_main_loop,
            )
