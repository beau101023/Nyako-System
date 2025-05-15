import threading
from abc import ABC
from queue import Queue

import numpy as np
import pyaudio
import pydub.playback
from pydub import AudioSegment
from torch import Tensor


class AudioPlayer(ABC):
    def play_audio(self, input_data: Tensor | np.ndarray | bytes | AudioSegment) -> None:
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


class PyAudioPlayer(AudioPlayer):
    def __init__(self, volume: float = 1.0):
        self.volume = volume
        self.audio_sys = pyaudio.PyAudio()

        # thread-safe FIFO queue + shutdown sentinel
        self._queue: Queue[AudioSegment | bytes | None] = Queue()

        # start the single playback thread
        self._playback_thread = threading.Thread(
            target=self._playback_loop, daemon=True
        )
        self._playback_thread.start()

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def play_audio(self, input_data: Tensor | np.ndarray | bytes | AudioSegment) -> None:
        """
        Queues audio data for playback.
        """
        if isinstance(input_data, AudioSegment):
            segment = input_data.apply_gain(self.volume)
            self._queue.put(segment)
        else:
            audio_bytes = audio_reformat(input_data, self.volume)
            self._queue.put(audio_bytes)

    def _playback_loop(self):
        """Background thread: block on FIFO queue, stop on None sentinel."""
        while True:
            item = self._queue.get()       # blocks until something is available
            if item is None:               # shutdown sentinel
                break

            # play audio
            if isinstance(item, AudioSegment):
                pydub.playback.play(item)
            else:
                stream = self.audio_sys.open(
                    format=pyaudio.paFloat32, channels=1, rate=48000, output=True
                )
                stream.write(item)
                stream.close()

    def close(self):
        """Gracefully stop playback thread."""
        self._queue.put(None)
        self._playback_thread.join()


def audio_reformat(input_data: Tensor | np.ndarray | bytes, volume: float = 1.0) -> bytes:
    """Apply volume to audio and convert to bytes format."""
    
    if isinstance(input_data, Tensor):
        audio_np: np.ndarray = input_data.numpy()
    elif isinstance(input_data, np.ndarray):
        audio_np = input_data
    elif isinstance(input_data, (bytes, bytearray)):
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
