import threading
from abc import ABC

import numpy as np
import pyaudio
from torch import Tensor


class Audio_Player(ABC):
    def play_audio(self, input_data: Tensor | np.ndarray | bytes) -> None:
        """
        Play audio from input data.

        Parameters:
        input_data: the audio data to play
        """

    def set_volume(self, volume: float) -> None:
        """
        Set the volume of the audio player.

        Parameters:
        volume (float): the volume to set
        """


class PyAudioPlayer(Audio_Player):
    def __init__(self, volume: float = 1.0):
        self.volume = volume
        self.audio_sys = pyaudio.PyAudio()

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def play_audio(self, input_data: Tensor | np.ndarray | bytes) -> None:
        audio_bytes = audioToBytes(input_data, self.volume)

        # Create a new thread for playing the audio
        thread = threading.Thread(target=self.playAudioInNewThread, args=(audio_bytes,))
        thread.start()

    def playAudioInNewThread(self, audio_bytes: bytes):
        """
        Spins off a new thread and plays a given audio byte array.

        Parameters:
        audio_bytes (bytes): the audio to play
        """

        # Play audio bytes
        stream = self.audio_sys.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True)

        stream.write(audio_bytes)
        stream.close()


def audioToBytes(input_data: Tensor | np.ndarray | bytes, volume: float = 1.0) -> bytes:
    # Check the type of the input data
    if isinstance(input_data, Tensor):
        # If it's a tensor, convert it to a numpy array
        audio_np: np.ndarray = input_data.numpy()
    elif isinstance(input_data, np.ndarray):
        # If it's a numpy array, use it directly
        audio_np = input_data
    elif isinstance(input_data, bytes):
        # If it's bytes, convert it to a numpy array
        audio_np = np.frombuffer(input_data, dtype=np.float32)
    else:
        raise TypeError(
            f"Input must be a tensor, numpy array, or bytes. Type is {type(input_data)}"
        )

    # Normalize audio
    audio_np = audio_np / np.max(audio_np)

    # Apply volume
    audio_np = audio_np * volume

    # Convert numpy array to bytes
    audio_bytes = audio_np.tobytes()

    return audio_bytes
