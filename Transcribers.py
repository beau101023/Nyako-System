from abc import ABC, abstractmethod

import numpy as np
import whisper_at as whisper
from faster_whisper import WhisperModel
from pydub import AudioSegment

from settings import INPUT_SAMPLING_RATE, device


class Transcriber(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def transcribe_speech(self, speech_buffer: AudioSegment, input_gain=1.0) -> str:
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
    def get_extra_tagging(self) -> list[str]:
        """
        Returns the extra labels supported by the transcriber.

        Returns:
        list: the extra labels supported by the transcriber
        """


class WhisperTranscriber(Transcriber):
    def __init__(
        self,
        no_speech_probability_threshold: float = 0.7,
        model_size: str = "small.en"
    ):
        """
        Create a new WhisperTranscriber

        Parameters:
        no_speech_probability_threshold (float): the threshold of likelihood after which the transcribed text will be rejected as not speech. Default is 0.7.
        model_size (str): the size of the Whisper model to load. Default is "small.en".
        """
        self.transcriber = whisper.load_model(model_size, device=device, in_memory=True)
        self.no_speech_probability_threshold = no_speech_probability_threshold
        self.result = None

    def transcribe_speech(self, speech_buffer: AudioSegment, input_gain=1.0):
        audio_segment = speech_buffer
        audio_segment = audio_segment.set_frame_rate(
            INPUT_SAMPLING_RATE
        )  # Set sampling rate to 16kHz
        audio_segment = audio_segment.set_channels(1)  # Set to mono
        audio_segment = audio_segment.set_sample_width(2)  # Set sample width to 16-bit (2 bytes)

        # Export the audio data to raw bytes
        audio_bytes = audio_segment.raw_data

        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("AudioSegment invalid.")

        # Convert the raw bytes to a numpy array of type int16
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).flatten().astype(np.float32) / 32768.0

        # apply input gain
        audio_np *= input_gain

        # run transcription
        try:
            self.result = self.transcriber.transcribe(
                audio_np, at_time_res=10, initial_prompt="Conversation between Nyako and Beau:"
            )
        except Exception as e:
            print(e)
            return "[speech unclear]"

        out_text = ""
        for segment in self.result["segments"]:
            if segment["no_speech_prob"] <= self.no_speech_probability_threshold:
                out_text += segment["text"]

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
            for segment_tuple in segment["audio tags"]:
                tags.add(segment_tuple[0])  # Extract the tag from the tuple

        return list(tags)  # Convert the set to a list


class FasterWhisperTranscriber(Transcriber):
    def __init__(
        self,
        no_speech_probability_threshold: float = 0.7,
        model_size: str = "small.en"
    ):
        """
        Create a new FasterWhisperTranscriber

        Note: The faster-whisper models seem to be best for batched processing of long audio.
            In this use case, for streaming audio, the performance differences are negligible
            compared to normal Whisper.

        Parameters:
        no_speech_probability_threshold (float): the threshold of likelihood after which the transcribed text will be rejected as not speech. Default is 0.7.
        model_size (str): the size of the FasterWhisper model to load. Default is "small.en".
        """
        self.model = WhisperModel(model_size, device=device.type, compute_type="auto")
        self.no_speech_probability_threshold = no_speech_probability_threshold
        self.result = None

    def transcribe_speech(self, speech_buffer: AudioSegment, input_gain=1.0):
        audio_segment = speech_buffer
        audio_segment = audio_segment.set_frame_rate(
            INPUT_SAMPLING_RATE
        )  # Set sampling rate to 16kHz
        audio_segment = audio_segment.set_channels(1)  # Set to mono
        audio_segment = audio_segment.set_sample_width(2)  # Set sample width to 16-bit (2 bytes)

        # Export the audio data to raw bytes
        audio_bytes = audio_segment.raw_data

        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("AudioSegment invalid.")

        # Convert the raw bytes to a numpy array of type int16
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).flatten().astype(np.float32) / 32768.0

        # apply input gain
        audio_np *= input_gain

        # run transcription
        try:
            self.result = self.model.transcribe(
                audio_np,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
                initial_prompt="Conversation between Nyako and Beau:",
            )
        except Exception as e:
            print(e)
            return "[speech unclear]"

        segments, _ = self.result

        out_text = ""
        for segment in segments:
            if segment.no_speech_prob <= self.no_speech_probability_threshold:
                out_text += segment.text

        return out_text

    def supports_extra_tagging(self):
        return False

    def get_extra_tagging(self) -> list[str]:
        raise RuntimeError("Extra tagging not supported on FasterWhisper")
