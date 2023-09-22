import torch
import numpy as np

from nyako_params import device

STT, STTdecoder, STTutils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                       model='silero_stt',
                                       jit_model='jit_xlarge',
                                       language='en', # also available 'de', 'es'
                                       device=device)

# accepts a bytes object containing raw audio data
# returns a string containing the decoded text
def handleSpeechToText(speechBuffer):
    speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)
    
    speechTensor = torch.tensor(speechBufferNumPyArray)
    
    # crashes unless tensor shape is [1, (audio length)], thus unsqueeze
    speechTensor.unsqueeze_(0)
    
    speechTensor = speechTensor.to(device)

    output = STT(speechTensor)

    # returns decoded text
    return STTdecoder(output[0].to(device))