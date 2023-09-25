import torch
import numpy as np

from ocotillo.api import Transcriber
from nyako_params import device
from nyako_params import INPUT_SAMPLING_RATE

if(device == 'cuda'):
    TSR = Transcriber(on_cuda=True)
else:
    TSR = Transcriber(on_cuda=False)

# accepts a bytes object containing raw audio data
# returns a string containing the decoded text
def handleSpeechToText(speechBuffer):
    speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)

    # returns decoded text
    return TSR.transcribe(speechTensor, sample_rate=INPUT_SAMPLING_RATE)