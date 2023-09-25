import pyaudio
import torchaudio
import io

p = pyaudio.PyAudio()

# play audio from a tensor
def playTTSAudio(audio_tensor):
    audio_bytesIO = io.BytesIO()
    torchaudio.save(audio_bytesIO, audio_tensor, sample_rate=48000, format='wav')

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=48000,
                    output=True)
    
    audio_bytesIO.seek(0)
    raw_wav = audio_bytesIO.read()

    stream.write(raw_wav)
    stream.close()

# debug function to play audio direct from bytes object
def playBuffer(buf):
    buf = np.frombuffer(buf, dtype=np.float32)
    display(Audio(buf, rate=16000))