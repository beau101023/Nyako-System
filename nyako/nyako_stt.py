import torch
import numpy as np

from ocotillo.api import Transcriber
from params import device
from params import INPUT_SAMPLING_RATE

if(device == 'cuda'):
    TSR = Transcriber(on_cuda=True)
else:
    TSR = Transcriber(on_cuda=False)

# accepts a bytes object containing raw audio data
# returns a string containing the decoded text
def transcribeSpeech(speechBuffer):
    speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)

    # returns decoded text
    return TSR.transcribe(speechBufferNumPyArray, sample_rate=INPUT_SAMPLING_RATE)