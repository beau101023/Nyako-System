import pyaudio
import io
import soundfile as sf


p = pyaudio.PyAudio()

# play audio from a tensor
def playTTSAudio(audio_tensor):
    audio_np = audio_tensor.numpy()

    #lower the volume
    audio_np = audio_np / 1.25

    # write to bytesio or the stream will only play the first teeny bit of audio
    audio = io.BytesIO()
    sf.write(audio, audio_np, 48000, format='wav', subtype='FLOAT')
    audio.seek(0)
    audio = audio.read()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=48000,
                    output=True)

    stream.write(audio)
    stream.close()