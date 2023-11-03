import torch
import numpy as np

# voice activity detection
VAD, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              onnx=True)

from params import INPUT_SAMPLING_RATE
def detectVoiceActivity(buf):
    return VAD(torch.from_numpy(np.frombuffer(buf, dtype=np.float32)), INPUT_SAMPLING_RATE).item()