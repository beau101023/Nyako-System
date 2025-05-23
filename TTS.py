from abc import ABC, abstractmethod

import numpy as np
import torch
from melo.api import TTS as meloModel
from overrides import override
from pydub import AudioSegment

from settings import device, language, model_id, sample_rate_out, speaker


class TextToSpeech(ABC):
    @abstractmethod
    def generate_speech(self, text: str) -> AudioSegment | None:
        """
        Generate speech from text input.

        Parameters:
        text (str): the text to generate speech from
        """

    @abstractmethod
    def warmup(self) -> None:
        """
        Optional method called to warm up the TTS.

        Can safely do nothing here.
        """


class SileroTTS(TextToSpeech):
    def __init__(self, speaker=speaker, sample_rate=sample_rate_out):
        self.speaker = speaker
        self.sample_rate = sample_rate

        self.model, _ = torch.hub.load(
            "snakers4/silero-models", "silero_tts", language=language, speaker=model_id
        )
        self.model.to(device)

    @override
    def warmup(self) -> None:
        self.model.apply_tts("t", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts("hi", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts("nyako", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts("test", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts(":D", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts("pbpbpb", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts("nyanya", speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts(
            "!my~jouyonaofj845q985:JLKJ^%:LKj", speaker=speaker, sample_rate=sample_rate_out
        )

    @override
    def generate_speech(self, text: str) -> AudioSegment | None:
        try:
            audio_tensor: torch.Tensor = self.model.apply_tts(
                text, speaker=self.speaker, sample_rate=self.sample_rate
            )
        except Exception as e:
            print("TTS failure. Error message: " + str(e) + "\n Input was: " + text)
            return None

        # Convert tensor to numpy array
        audio_data_np: np.ndarray = audio_tensor.numpy()

        # Scale to the range of 16-bit PCM audio
        audio_data_np = np.int16(audio_data_np * 32767)  # type: ignore

        # Create an audio segment from the numpy array
        audio_segment = AudioSegment(
            audio_data_np.tobytes(),  # data
            frame_rate=self.sample_rate,  # sample rate
            sample_width=2,  # 16 bit
            channels=1,  # mono
        )

        return audio_segment


class MeloTTS(TextToSpeech):
    def __init__(self, speaker=speaker, sample_rate=sample_rate_out):
        self.speaker = speaker
        self.sample_rate = sample_rate

        self.model = meloModel(language="EN", device=device.type)
        self.speaker_ids = self.model.hps.data.spk2id

    @override
    def warmup(self) -> None:
        self.model.tts_to_file("HIHIHI", self.speaker_ids["EN-US"], speed=1.0, quiet=True)

    @override
    def generate_speech(self, text: str) -> AudioSegment | None:
        audio_data_np: np.ndarray = self.model.tts_to_file(
            text, self.speaker_ids["EN-US"], speed=1.0, quiet=True
        )

        # Scale to the range of 16-bit PCM audio
        audio_data_np = np.int16(audio_data_np * 32767)  # type: ignore

        # Create an audio segment from the numpy array
        audio_segment = AudioSegment(
            audio_data_np.tobytes(),  # data
            frame_rate=self.model.hps.data.sampling_rate,  # sample rate
            sample_width=2,  # 16 bit
            channels=1,  # mono
        )

        audio_segment.set_frame_rate(self.sample_rate)

        return audio_segment
