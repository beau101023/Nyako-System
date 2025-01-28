import threading
import asyncio

from TTS import TextToSpeech

from audio_playback import Audio_Player
from audio_playback import PyAudioPlayer


from event_system import EventBusSingleton
from event_system.events.System import StartupEvent, StartupStage
from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType, OutputDeliveryEvent
from event_system.events.Audio import AudioDirection, VolumeUpdatedEvent, AudioType, SpeakingStateUpdate

from pipesys import Pipe, MessageSource


class TextToSpeechOutput(Pipe):
    text_to_speech: TextToSpeech
    audio_player: Audio_Player

    def __init__(self):
        self.volume: float = 1.0

    @classmethod
    async def create(cls, listen_to: MessageSource, speech_to_text: TextToSpeech=SileroRVC_TTS(), audio_player: Audio_Player=PyAudioPlayer()):
        self = TextToSpeechOutput()

        self.text_to_speech = speech_to_text
        self.audio_player = audio_player

        # subscribe to events
        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.onWarmup)
        self.subscribeAll(listen_to, self.onMessage)
        EventBusSingleton.subscribe(VolumeUpdatedEvent(audio_type=AudioType.SYSTEM, audio_direction=AudioDirection.OUTPUT), self.onVolumeUpdate)

        # notify system that tts is ready
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.VOICE, True))

        return self

    async def onMessage(self, event: MessageEvent):
        msg = event.message

        # tts breaks if you send it nothing
        if msg == None or msg == "" or msg == " ":
            return
        
        # avoid blocking with speech output processing
        thread = threading.Thread(target=self.say, args=(msg,asyncio.get_event_loop()))
        thread.start()

    async def onVolumeUpdate(self, event: VolumeUpdatedEvent):
        if event.volume == None:
            return

        self.audio_player.set_volume(event.volume)

    def say(self, text, loop):
        audio = self.text_to_speech.generate_speech(text)

        if audio == None:
            return

        self.audio_player.play_audio(audio)
        asyncio.run_coroutine_threadsafe(
            EventBusSingleton.publish(OutputDeliveryEvent(message=text, sender=self)),
            loop
        )

    def onWarmup(self, event: StartupEvent):
        self.text_to_speech.warmup()

    async def publishSpeakingStart(self):
        await EventBusSingleton.publish(SpeakingStateUpdate(True, AudioType.SYSTEM, AudioDirection.OUTPUT))

    async def publishSpeakingEnd(self):
        await EventBusSingleton.publish(SpeakingStateUpdate(False, AudioType.SYSTEM, AudioDirection.OUTPUT))
