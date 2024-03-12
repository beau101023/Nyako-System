import torch
from audio_playback import playAudio

from rvc_pipe.rvc_infer import rvc_convert

import soundfile as sf
from io import FileIO
import timeit

from params import sample_rate_out, language, model_id, speaker, device

model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
model.to(device)

# text to raw audio
def say(text, volume=1.0):

    start_time = timeit.default_timer()
    try:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
    except Exception as e:
        print("TTS failure. Error message: " + str(e) + "\n Input was: " + text)
        return
    
    print("model 1 inference time: " + str(timeit.default_timer() - start_time))

    playAudio(audio_tensor, volume=volume)

def sayWithRVC(text, volume=1.0):

    start_time = timeit.default_timer()
    try:
        audio_tensor = model.apply_tts(text, speaker=speaker, sample_rate=sample_rate_out)
    except Exception as e:
        print("TTS failure. Error message: " + str(e) + "\n Input was: " + text)
        return
    
    print("model 1 inference time: " + str(timeit.default_timer() - start_time))

    # normalize
    audio_np = audio_tensor.numpy()
    audio_np = audio_np / audio_np.max()

    start_time = timeit.default_timer()

    # bounce to wav
    with sf.SoundFile(FileIO('nyako/inference_temp/voice.wav', 'wb'), mode='w', samplerate=48000, channels=1, format='wav', subtype='FLOAT') as f:
        f.write(audio_np)
    
    print("model 1 wav write time: " + str(timeit.default_timer() - start_time))

    start_time = timeit.default_timer()

    # convert with rvc
    rvc_convert(f0_up_key=4, model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    
    print("model 2 inference time: " + str(timeit.default_timer() - start_time))

    start_time = timeit.default_timer()

    with sf.SoundFile('nyako/inference_temp/voice_conv.wav', mode='r') as f:
        audio = f.read(dtype='float32')

    print("model 2 wav read time: " + str(timeit.default_timer() - start_time))

    print("playing audio")
    playAudio(audio, volume=volume)

# torch optimizer warmup
def warmup():
    rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_dir_path='nyako/inference_temp/voice_conv.wav')
    
    # bunch of warm up steps cause the torch auto optimizer only kicks in after so many passes
    # have not actually figured out precisely how many steps are needed
    # without warmup: inference time on the order of 3-5 seconds
    # with warmup: inference time on the order of 0.25 seconds
    model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('hi', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('nyako', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('test', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts(':D', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('pbpbpb', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('nyanya', speaker=speaker, sample_rate=sample_rate_out)
    model.apply_tts('!my~jouyonaofj845q985:JLKJ^%:LKj', speaker=speaker, sample_rate=sample_rate_out)