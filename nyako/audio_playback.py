from abc import ABC, abstractmethod

import pyaudio
import numpy as np
import torch

import threading

class Audio_Player(ABC):
    def play_audio(self, input_data):
        """
        Play audio from input data.

        Parameters:
        input_data: the audio data to play
        """

class PyAudioPlayer(Audio_Player):
    def __init__(self, volume: float = 1.0):
        self.volume = volume
        self.audio_sys = pyaudio.PyAudio()

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def play_audio(self, input_data):
        audio_bytes = self.audioToBytes(input_data)

        # Create a new thread for playing the audio
        thread = threading.Thread(target=self.playAudioThread, args=(audio_bytes,))
        thread.start()

    def audioToBytes(self, input_data, volume=1.0):
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
            raise TypeError(f"Input must be a tensor, numpy array, or bytes. Type is {type(input_data)}")

        # Normalize audio
        audio_np = audio_np / np.max(audio_np)

        # Apply volume
        audio_np = audio_np * volume

        # Convert numpy array to bytes
        audio_bytes = audio_np.tobytes()

        return audio_bytes

    def playAudioThread(self, audio_bytes):
        # Play audio bytes
        stream = self.audio_sys.open(format=pyaudio.paFloat32,
                                        channels=1,
                                        rate=48000,
                                        output=True)

        stream.write(audio_bytes)
        stream.close()