import numpy as np

from ocotillo.api import Transcriber
from params import device
from params import INPUT_SAMPLING_RATE

from threading import Thread
from queue import Queue

# accepts a bytes object containing raw audio data
# returns a string containing the decoded text
def transcribeSpeech(speechBuffer, transcriber: Transcriber, input_gain=1.0):
    speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)

    # apply input gain
    speechBufferNumPyArray *= input_gain

    # returns decoded text
    return transcriber.transcribe(speechBufferNumPyArray, sample_rate=INPUT_SAMPLING_RATE)

# transcriber object pool to avoid the overhead of spinning up a new transcriber on demand
#  one transcriber is required for every audio stream because transcribers may be stateful
class TranscriberPool:
    def __init__(self, spare_transcribers=2):
        self.pool = {}
        self.overflow_pool_size = spare_transcribers
        self.overflow_pool: Queue = Queue()
        
        for i in range(spare_transcribers):
            self.initializeTranscriber()

    def getTranscriber(self, user_id):
        transcriber = None

        if user_id in self.pool:
            transcriber = self.pool[user_id]
        elif len(self.overflow_pool) > 0:
            transcriber = self.overflow_pool.get()
            self.pool[user_id] = transcriber
        else:
            # failure/fallback case
            self.initializeTranscriber()
            transcriber = self.overflow_pool.get()
            self.pool[user_id] = transcriber

        if len(self.overflow_pool) < self.overflow_pool_size:
            thread = Thread(target=self.threadInitializeTranscriber, args=(self.overflow_pool_size-len(self.overflow_pool),))
            thread.start()

        if transcriber is None:
            raise Exception("Transcriber is None")

    def threadInitializeTranscriber(self, amt: int):
        for i in range(amt):
            self.initializeTranscriber()

    def initializeTranscriber(self):
        if device == 'cuda':
            self.overflow_pool.put(Transcriber(on_cuda=True))
        else:
            self.overflow_pool.put(Transcriber(on_cuda=False))