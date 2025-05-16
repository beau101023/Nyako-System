import numpy as np
import pydub
import torch

from settings import INPUT_SAMPLING_RATE

# voice activity detection
VAD, _ = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", onnx=True)


def detectVoiceActivity(buf) -> float:
    if isinstance(buf, torch.Tensor):
        return VAD(buf, INPUT_SAMPLING_RATE).item()

    elif isinstance(buf, (bytes, bytearray)):
        return VAD(
            torch.from_numpy(np.frombuffer(buf, dtype=np.int16).astype(np.float32)), INPUT_SAMPLING_RATE
        ).item()

    elif isinstance(buf, pydub.AudioSegment):
        # Convert the AudioSegment to 16kHz, mono, 16-bit little-endian PCM format
        audio_segment = buf
        audio_segment = audio_segment.set_frame_rate(16000)  # Set sampling rate to 16kHz
        audio_segment = audio_segment.set_channels(1)  # Set to mono
        audio_segment = audio_segment.set_sample_width(2)  # Set sample width to 16-bit (2 bytes)

        # Export the audio data to raw bytes
        audio_bytes = audio_segment.raw_data

        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("AudioSegment invalid.")

        # Convert the raw bytes to a numpy array of type int16
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Convert the numpy array to a torch tensor
        audio_tensor = torch.from_numpy(audio_np).float() / 32768.0  # Normalize to [-1, 1]

        # Pass the tensor to the VAD model and get the result
        return VAD(audio_tensor, INPUT_SAMPLING_RATE).item()
    else:
        raise RuntimeError("Uhh.. idk man")
