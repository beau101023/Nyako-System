import pyaudio
import numpy as np
import torch

import threading

def playAudio(input_data, volume=1.0):
    audio_bytes = audioToBytes(input_data, volume=volume)

    # Create a new thread for playing the audio
    thread = threading.Thread(target=playAudioThread, args=(audio_bytes,))
    thread.start()

def playAudioThread(audio_bytes):
    # Play audio bytes
    stream = pyaudio.PyAudio().open(format=pyaudio.paFloat32,
                                    channels=1,
                                    rate=48000,
                                    output=True)

    stream.write(audio_bytes)
    stream.close()

def audioToBytes(input_data, volume=1.0):
    # Check the type of the input data
    if isinstance(input_data, torch.Tensor):
        # If it's a tensor, convert it to a numpy array
        audio_np = input_data.numpy()
    elif isinstance(input_data, np.ndarray):
        # If it's a numpy array, use it directly
        audio_np = input_data
    elif isinstance(input_data, bytes):
        # If it's bytes, convert it to a numpy array
        audio_np = np.frombuffer(input_data, dtype=np.float32)
    else:
        raise TypeError("Input must be a tensor, numpy array, or bytes")

    # Normalize audio
    audio_np = audio_np / np.max(audio_np)

    # Apply volume
    audio_np = audio_np * volume

    # Convert numpy array to bytes
    audio_bytes = audio_np.tobytes()

    return audio_bytes