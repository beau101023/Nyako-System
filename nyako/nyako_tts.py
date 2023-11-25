import torch
from audio_playback import playAudioTensor
from audio_playback import playAudioBytes

from rvc_pipe.rvc_infer import rvc_convert

import soundfile as sf
from io import FileIO

from params import sample_rate_out, language, model_id, speaker, device

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
model.to(device)

# text to raw audio
def say(text, ssml=False):
    try:
        if(ssml):
            audio_tensor = model.apply_tts(ssml_text=text, speaker=speaker, sample_rate=sample_rate_out)
        else:
            audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
    except Exception as e:
        print("TTS failure. Message: " + e.args[0])
        return

    playAudioTensor(audio_tensor)

async def sayWithRVC(text):

    try:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
    except Exception as e:
        print("TTS failure. Message: " + text)
        return

    # normalize
    audio_np = audio_tensor.numpy()
    audio_np = audio_np / audio_np.max()

    print("model 1 inference success")

    # bounce to wav
    with sf.SoundFile(FileIO('nyako/inference_temp/voice.wav', 'wb'), mode='w', samplerate=48000, channels=1, format='wav', subtype='FLOAT') as f:
        f.write(audio_np)
    
    print("file written")

    # convert with rvc
    rvc_convert(f0_up_key=6, model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    
    with sf.SoundFile('nyako/inference_temp/voice_conv.wav', mode='r') as f:
        audio = f.read(dtype='float32')

    playAudioBytes(audio.tobytes())

# torch optimizer warmup
def warmup():
    rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)