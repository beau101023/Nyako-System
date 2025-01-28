import discord
import asyncio

from pydub import AudioSegment

from io import BytesIO

from TTS import TextToSpeech, SileroTTS

from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Discord import VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from event_system.events.Audio import AudioDirection, SpeakingStateUpdate, AudioType
from event_system.events.Pipeline import OutputDeliveryEvent

from event_system.events.System import StartupEvent, StartupStage, TaskCreatedEvent
from pipesys.Pipe import Pipe, MessageSource

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
    async def create(cls, listen_to: MessageSource, speech_to_text: TextToSpeech=SileroTTS()):
        self = DiscordVoiceOutput()

        self.text_to_speech = speech_to_text

        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.onWarmup)
        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.onVoiceChannelConnected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.onVoiceChannelDisconnected)
        self.subscribeAll(listen_to, self.handleMessage)

        EventBusSingleton.subscribe(SpeakingStateUpdate(audio_direction=AudioDirection.INPUT), self.onUserSpeakingStateChange)
        task = asyncio.create_task(self.playback_loop())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Voice Output Playback"))

        return self
    
    def onWarmup(self, event: StartupEvent):
        self.text_to_speech.warmup()
    
    async def onVoiceChannelConnected(self, event: VoiceChannelConnectedEvent):
        self.voice_connection = event.voice_client

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, True))

    async def onVoiceChannelDisconnected(self, event: VoiceChannelDisconnectedEvent):
        self.voice_connection = None

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, False))

    async def onUserSpeakingStateChange(self, event: SpeakingStateUpdate):
        # when user starts speaking, call the interrupt method
        if event.is_speaking:
            await self.interruptSpeech()

    async def interruptSpeech(self):
        if self.voice_connection and self.voice_connection.is_playing():
            self.voice_connection.stop()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

    async def handleMessage(self, event: MessageEvent):
        if not self.voice_connection or not event.message:
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
                after=lambda e: self.finishedPlayingCallback(e, message),
                wait_finish=False
            )

    def convert_for_output(self, audio_segment: AudioSegment) -> AudioSegment:
        return audio_segment.set_channels(2).set_frame_rate(48000).set_sample_width(2)

    def finishedPlayingCallback(self, ex: Exception | None, message: str):
        asyncio.run_coroutine_threadsafe(
            EventBusSingleton.publish(SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.OUTPUT)),
            self.asyncio_main_loop
        )
        if ex is None:
            asyncio.run_coroutine_threadsafe(
                EventBusSingleton.publish(OutputDeliveryEvent(message=message)),
                self.asyncio_main_loop
            )