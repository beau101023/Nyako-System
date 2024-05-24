import discord

from nyako.TTS import TextToSpeech
from nyako.TTS import SileroRVC_TTS

from event_system.EventBusSingleton import EventBusSingleton

from event_system.events.Discord import VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent
from event_system.events.Pipeline import MessageEvent
from event_system.events.System import OutputAvailableUpdate, SystemOutputType

from pipesys.Pipe import OutputPipe, Pipe

class DiscordVoiceOutput(OutputPipe):
    """
    Module that recieves text input from a pipe, converts it to speech, and plays it on the discord voice channel the bot is currently connected to.
    """

    text_to_speech: TextToSpeech
    discord_client: discord.Client
    voice_connection: discord.VoiceClient

    def __init__(self):
        self.voice_connection = None

    @classmethod
    async def create(cls, discord_client, listen_to: Pipe, speech_to_text: TextToSpeech=SileroRVC_TTS()):
        self = DiscordVoiceOutput()

        self.discord_client = discord_client
        self.text_to_speech = speech_to_text

        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.onVoiceChannelConnected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.onVoiceChannelDisconnected)
        EventBusSingleton.subscribe(MessageEvent(None, listen_to), self.handleMessage)

        return self
    
    async def onVoiceChannelConnected(self, event: VoiceChannelConnectedEvent):
        self.voice_connection = event.client

        await EventBusSingleton.publish(OutputAvailableUpdate(SystemOutputType.DISCORD_VOICE, True))

    async def onVoiceChannelDisconnected(self, event: VoiceChannelDisconnectedEvent):
        self.voice_connection = None

        await EventBusSingleton.publish(OutputAvailableUpdate(SystemOutputType.DISCORD_VOICE, False))

    async def handleMessage(self, event: MessageEvent):
        if self.voice_connection == None:
            return

        audio = self.text_to_speech.generate_speech(event.message)

        self.voice_connection.play(discord.PCMAudio(audio))



        