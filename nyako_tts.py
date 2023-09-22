import torch
from audio_playback import playTTSAudio

from nyako_params import sample_rate_out, language, model_id, speaker

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)

from nyako_params import device
model.to(device)

# text to raw audio
def say(text, ssml=False):
    if(ssml):
        audio_tensor = model.apply_tts(ssml_text=text, speaker=speaker, sample_rate=sample_rate_out)
    else:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
    audio_tensor.unsqueeze_(0)

    playTTSAudio(audio_tensor)

# torch optimizer triggers at second call and hangs for 200 seconds
# so we do a dry run first
# not good!
def warmup():
    model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)