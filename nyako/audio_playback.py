import pyaudio


p = pyaudio.PyAudio()

# play audio from a tensor
def playAudioTensor(audio_tensor):
    audio_np = audio_tensor.numpy()

    #normalize audio
    audio_np = audio_np / audio_np.max()

    # ow, my ears
    audio_np /= 2.0

    playAudioBytes(audio_np.tobytes())

# play raw audio bytes
def playAudioBytes(audio_bytes):
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=48000,
                    output=True)

    stream.write(audio_bytes)
    stream.close()