import torch
import nyako_tts
from params import sample_rate_out, language, model_id, speaker, device
from EventTopics import Topics
from EventBus import EventBus
import asyncio
import threading

from params import advanced_voice_enabled

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
model.to(device)

class TextToSpeechOutput:
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus: EventBus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY):
        self = TextToSpeechOutput()

        # init
        self.tag = "voice"
        self.volume: float = 1.0
        self.event_bus = event_bus

        # subscribe to events
        self.event_bus.subscribe(self.onWarmup, Topics.System.WARMUP)
        self.event_bus.subscribe(self.onMessage, listen_topic)
        self.event_bus.subscribe(self.onVolumeUpdate, Topics.Audio.OUTPUT_VOLUME_UPDATE)

        # notify system that tts is ready
        stateUpdate = Topics.OutputStateUpdate(self.tag, True)
        await self.event_bus.publish(Topics.System.OUTPUT_STATE, stateUpdate)

        return self

    async def onMessage(self, message: str):
        # tts breaks if you send it nothing
        if message == None or message == "" or message == " ":
            return
        
        # avoid blocking with speech output processing
        thread = threading.Thread(target=self.say, args=(message,))
        thread.start()

    async def onVolumeUpdate(self, event: Topics.VolumeUpdate):
        self.volume = event.volume

    def say(self, text):
        if(advanced_voice_enabled):
            nyako_tts.sayWithRVC(text, volume=self.volume)
            return
        else:
            nyako_tts.say(text, volume=self.volume)
            return
        

    def onWarmup(self):
        nyako_tts.warmup()

    async def publishSpeakingStart(self):
        update = Topics.SpeakingStateUpdate(starting=True)
        await self.event_bus.publish(Topics.TTS.SPEAKING_STATE, update)

    async def publishSpeakingEnd(self):
        update = Topics.SpeakingStateUpdate(ending=True)
        await self.event_bus.publish(Topics.TTS.SPEAKING_STATE, update)
