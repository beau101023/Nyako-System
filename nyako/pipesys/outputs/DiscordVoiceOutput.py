import discord
import asyncio

from pydub import AudioSegment

from io import BytesIO

from TTS import TextToSpeech, SileroRVC_TTS

from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Discord import VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType
from event_system.events.Audio import AudioDirection, SpeakingStateUpdate, AudioType

from pipesys.Pipe import OutputPipe, Pipe

class DiscordVoiceOutput(OutputPipe):
    """
    Module that recieves text input from a pipe, converts it to speech, and plays it on the discord voice channel the bot is currently connected to.
    """

    text_to_speech: TextToSpeech
    voice_connection: discord.VoiceClient | None = None
    asyncio_main_loop: asyncio.AbstractEventLoop

    def __init__(self):
        self.voice_connection = None
        self.asyncio_main_loop = asyncio.get_event_loop()

    @classmethod
    async def create(cls, listen_to: MessageSource, speech_to_text: TextToSpeech=SileroTTS()):
        self = DiscordVoiceOutput()

        self.text_to_speech = speech_to_text

        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.onVoiceChannelConnected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.onVoiceChannelDisconnected)
        self.subscribeAll(listen_to, self.handleMessage)

        return self
    
    async def onVoiceChannelConnected(self, event: VoiceChannelConnectedEvent):
        self.voice_connection = event.voice_client

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, True))

    async def onVoiceChannelDisconnected(self, event: VoiceChannelDisconnectedEvent):
        self.voice_connection = None

        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.DISCORD_VOICE, False))

    async def handleMessage(self, event: MessageEvent):
        if self.voice_connection == None or event.message == None:
            return

        audio = self.text_to_speech.generate_speech(event.message)

        if audio == None:
            return
        
        audio = self.convert_for_output(audio).raw_data

        if not isinstance(audio, bytes):
            return

        audio = BytesIO(audio)

        await EventBusSingleton.publish(SpeakingStateUpdate(True, AudioType.DISCORD, AudioDirection.OUTPUT))
        
        # If audio's already playing and we queue a new message, interrupt it and play the new audio instead of
        #   building up a message backlog or anything
        if self.voice_connection.is_playing():
            self.voice_connection.stop()

        self.voice_connection.play(discord.PCMAudio(audio), after= self.finishedPlayingCallback)

    def convert_for_output(self, audio_segment: AudioSegment) -> AudioSegment:
        return audio_segment.set_channels(2).set_frame_rate(48000).set_sample_width(2)

    def finishedPlayingCallback(self, ex: Exception | None):
        asyncio.run_coroutine_threadsafe(
            EventBusSingleton.publish(SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.INPUT)),
            self.asyncio_main_loop)