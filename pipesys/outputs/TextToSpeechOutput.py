import asyncio
import threading

from audio_playback import AudioPlayer, PyAudioPlayer
from event_system import EventBusSingleton
from event_system.events.Audio import (
    AudioDirection,
    AudioType,
    SpeakingStateUpdate,
    VolumeUpdatedEvent,
)
from event_system.events.Pipeline import (
    MessageEvent,
    OutputAvailabilityEvent,
    OutputDeliveryEvent,
    SystemOutputType,
)
from event_system.events.System import StartupEvent, StartupStage
from pipesys import MessageSource, Pipe
from TTS import MeloTTS, TextToSpeech


class TextToSpeechOutput(Pipe):
    text_to_speech: TextToSpeech
    audio_player: AudioPlayer

    def __init__(self):
        self.volume: float = 1.0

    @classmethod
    async def create(
        cls,
        listen_to: MessageSource,
        text_to_speech: TextToSpeech = MeloTTS(),
        audio_player: AudioPlayer = PyAudioPlayer(),
    ):
        self = TextToSpeechOutput()

        self.text_to_speech = text_to_speech
        self.audio_player = audio_player

        # subscribe to events
        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.on_warmup)
        self.subscribe_to_message_sources(listen_to, self.on_message)
        EventBusSingleton.subscribe(
            VolumeUpdatedEvent(audio_type=AudioType.SYSTEM, audio_direction=AudioDirection.OUTPUT),
            self.on_volume_update,
        )

        # notify system that tts is ready
        await EventBusSingleton.publish(OutputAvailabilityEvent(SystemOutputType.VOICE, True))

        return self

    async def on_message(self, event: MessageEvent):
        msg = event.message

        # tts breaks if you send it nothing
        if msg is None or msg == "" or msg == " ":
            return

        # avoid blocking with speech output processing
        thread = threading.Thread(target=self.say, args=(msg, asyncio.get_event_loop()))
        thread.start()

    async def on_volume_update(self, event: VolumeUpdatedEvent):
        if not isinstance(event.volume, float):
            return

        self.audio_player.set_volume(event.volume)

    def say(self, text, loop):
        audio = self.text_to_speech.generate_speech(text)

        if audio is None:
            return

        self.audio_player.play_audio(audio)
        asyncio.run_coroutine_threadsafe(
            EventBusSingleton.publish(OutputDeliveryEvent(message=text, sender=self)), loop
        )

    def on_warmup(self, event: StartupEvent):
        self.text_to_speech.warmup()

    async def publish_speaking_start(self):
        await EventBusSingleton.publish(
            SpeakingStateUpdate(True, AudioType.SYSTEM, AudioDirection.OUTPUT)
        )

    async def publish_speaking_end(self):
        await EventBusSingleton.publish(
            SpeakingStateUpdate(False, AudioType.SYSTEM, AudioDirection.OUTPUT)
        )
