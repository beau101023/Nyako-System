from abc import ABC, abstractmethod

import numpy as np

import whisper_at as whisper
from ocotillo.api import Transcriber as OcotilloSTT

from params import device
from params import INPUT_SAMPLING_RATE

from threading import Thread
from queue import Queue

from typing import List

class Transcriber(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def transcribeSpeech(self, speechBuffer, input_gain=1.0) -> str:
        """
        Transcribes a section of audio data using the provided transcriber object, with the specified input gain.

        Parameters:
        speechBuffer (bytes): a bytes object containing the audio data
        input_gain (float): a float representing the input gain. Default is 1.0.

        Returns:
        Transcription of the speech.
        """

    @abstractmethod
    def supports_extra_tagging(self) -> bool:
        """
        Returns whether the transcriber supports extra labels.

        Returns:
        bool: whether the transcriber supports extra labels
        """

    @abstractmethod
    def get_extra_tagging(self) -> List[str]:
        """
        Returns the extra labels supported by the transcriber.

        Returns:
        list: the extra labels supported by the transcriber
        """

class WhisperTranscriber(Transcriber):
    def __init__(self, no_speech_probability_threshold:float = 0.7):
        self.transcriber = whisper.load_model("large-v1", device=device, in_memory=True)
        self.no_speech_probability_threshold = no_speech_probability_threshold
        self.result = None

    def transcribeSpeech(self, speechBuffer, input_gain=1.0):
        speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)

        # apply input gain
        speechBufferNumPyArray *= input_gain

        # run transcription
        self.result = self.transcriber.transcribe(speechBufferNumPyArray, at_time_res=2, initial_prompt="Glossary: Nyako, Beau, based, ayo, cringe")

        out_text = ""
        for segment in self.result['segments']:
            if(segment['no_speech_prob'] <= self.no_speech_probability_threshold):
                out_text += segment['text']

        return out_text
    
    def supports_extra_tagging(self):
        return True
    
    def get_extra_tagging(self):
        audio_tag_result = whisper.parse_at_label(self.result, top_k=2, p_threshold=-2)
    
        tags = set()
        for segment in audio_tag_result:
            for segment_tuple in segment['audio tags']:
                tags.add(segment_tuple[0])  # Extract the tag from the tuple
    
        return list(tags)  # Convert the set to a list

class OcotilloTranscriber(Transcriber):
    def __init__(self):
        self.transcriber = OcotilloSTT(on_cuda=device == 'cuda')

    def transcribeSpeech(self, speechBuffer, input_gain=1.0):
        speechBufferNumPyArray = np.fromstring(speechBuffer, dtype=np.float32)

        # apply input gain
        speechBufferNumPyArray *= input_gain

        # returns decoded text
        return self.transcriber.transcribe(speechBufferNumPyArray, sample_rate=INPUT_SAMPLING_RATE)
    
    def supports_extra_tagging(self):
        return False
    
    def get_extra_tagging(self):
        return []
    
    def supports_speech_probability(self):
        return False
    
    def get_speech_probability(self) -> float:
        return 0.0

from typing import Type
from typing import Dict

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