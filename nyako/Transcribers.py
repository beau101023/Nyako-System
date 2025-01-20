from abc import ABC, abstractmethod

from pydub import AudioSegment

import numpy as np

import whisper_at as whisper

from params import device
from params import INPUT_SAMPLING_RATE

from typing import List

class Transcriber(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def transcribeSpeech(self, speechBuffer: AudioSegment, input_gain=1.0) -> str:
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
        """
        Create a new WhisperTranscriber

        Parameters:
        no_speech_probability_threshold (float): the theshold of likelihood after which the transcribed text will be rejected as not speech. Default is 0.7.
        """
        self.transcriber = whisper.load_model("small.en", device=device, in_memory=True)
        self.no_speech_probability_threshold = no_speech_probability_threshold
        self.result = None

    def transcribeSpeech(self, speechBuffer: AudioSegment, input_gain=1.0):

        audio_segment = speechBuffer
        audio_segment = audio_segment.set_frame_rate(INPUT_SAMPLING_RATE)  # Set sampling rate to 16kHz
        audio_segment = audio_segment.set_channels(1)        # Set to mono
        audio_segment = audio_segment.set_sample_width(2)    # Set sample width to 16-bit (2 bytes)

        # Export the audio data to raw bytes
        audio_bytes = audio_segment.raw_data

        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("AudioSegment invalid.")

        # Convert the raw bytes to a numpy array of type int16
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).flatten().astype(np.float32) / 32768.0

        # apply input gain
        audio_np *= input_gain

        # run transcription
        self.result = self.transcriber.transcribe(audio_np, at_time_res=2, initial_prompt="Glossary: Nyako, Beau, based, ayo, cringe")

        out_text = ""
        for segment in self.result['segments']:
            if(segment['no_speech_prob'] <= self.no_speech_probability_threshold):
                out_text += segment['text']

        tags = self.get_extra_tagging()
        tags_string = ", ".join(tags)  # Convert the list of tags to a string
        out_text = f"(Audio: {tags_string})" + out_text  # Prepend the tags to the transcript

        return out_text
    
    def supports_extra_tagging(self):
        return True
    
    def get_extra_tagging(self) -> list[str]:
        audio_tag_result = whisper.parse_at_label(self.result, top_k=2, p_threshold=-2)
    
        tags = set()
        for segment in audio_tag_result:
            for segment_tuple in segment['audio tags']:
                tags.add(segment_tuple[0])  # Extract the tag from the tuple
    
        return list(tags)  # Convert the set to a list