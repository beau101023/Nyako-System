import asyncio
import torch
from audio_playback import playTTSAudio
from params import sample_rate_out, language, model_id, speaker, device
from module_system.core.listener import Listener

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
model.to(device)

class TextToSpeechOutput(Listener):
    def __init__(self):
        super().__init__()

    async def receive(self, message: str):
        self.say(message)

    def say(self, text, ssml=False):
        #if(ssml):
        #    audio_tensor = model.apply_tts(ssml_text=text, speaker=speaker, sample_rate=sample_rate_out)
        #else:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
        audio_tensor.unsqueeze_(0)

        playTTSAudio(audio_tensor)

    def warmup(self):
        model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
        model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)

    speakingStartListeners = []
    async def whenSpeakingStarts(self, listener_method):
        self.speakingStartListeners.append(listener_method)

    async def speakingStart(self):
        for listener_method in self.speakingStartListeners:
            await listener_method()

    speakingEndListeners = []
    async def whenSpeakingEnds(self, listener_method):
        self.speakingEndListeners.append(listener_method)

    async def speakingEnd(self):
        for listener_method in self.speakingEndListeners:
            await listener_method()
