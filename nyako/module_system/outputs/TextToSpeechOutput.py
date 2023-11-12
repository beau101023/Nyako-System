import torch
from audio_playback import playTTSAudio
from params import sample_rate_out, language, model_id, speaker, device
from EventTopics import Topics
from EventBus import EventBus

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
model.to(device)

class TextToSpeechOutput:
    event_bus: EventBus

    @classmethod
    async def create(cls, event_bus: EventBus):
        self = TextToSpeechOutput()
        self.tag = "voice"
        self.event_bus = event_bus
        self.event_bus.subscribe(self.warmup, Topics.System.PRE_LINKING)
        stateUpdate = Topics.OutputStateUpdate(self.tag, True)
        await self.event_bus.publish(Topics.System.OUTPUT_STATE, stateUpdate)
        return self

    async def onMessage(self, message: str):
        await self.speakingStart()
        self.say(message)
        await self.speakingEnd()


    def say(self, text, ssml=False):
        #if(ssml):
        #    audio_tensor = model.apply_tts(ssml_text=text, speaker=speaker, sample_rate=sample_rate_out)
        #else:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)

        playTTSAudio(audio_tensor)

    def warmup(self):
        model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
        model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)

    async def speakingStart(self):
        update = Topics.SpeakingStateUpdate(starting=True)
        await self.event_bus.publish(Topics.TTS.SPEAKING_STATE, update)

    async def speakingEnd(self):
        update = Topics.SpeakingStateUpdate(ending=True)
        await self.event_bus.publish(Topics.TTS.SPEAKING_STATE, update)
