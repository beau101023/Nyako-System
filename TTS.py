from abc import ABC, abstractmethod
from io import FileIO

import numpy as np

from pydub import AudioSegment

from overrides import override
import torch
import soundfile as sf

# disabled as rvc_infer requires running as admin
# from rvc_pipe.rvc_infer import rvc_convert

from settings import sample_rate_out, language, model_id, speaker, device

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

        self.model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
        self.model.to(device)

    @override
    def warmup(self) -> None:
        self.model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('hi', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('nyako', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('test', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts(':D', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('pbpbpb', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('nyanya', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('!my~jouyonaofj845q985:JLKJ^%:LKj', speaker=speaker, sample_rate=sample_rate_out)

    @override
    def generate_speech(self, text: str) -> AudioSegment | None:
        try:
            audio_tensor: torch.Tensor = self.model.apply_tts(text, speaker=self.speaker, sample_rate=self.sample_rate)
        except Exception as e:
            print("TTS failure. Error message: " + str(e) + "\n Input was: " + text)
            return None

        # Convert tensor to numpy array
        audio_data_np: np.ndarray = audio_tensor.numpy()

        # Scale to the range of 16-bit PCM audio
        audio_data_np = np.int16(audio_data_np * 32767) # type: ignore

        # Create an audio segment from the numpy array
        audio_segment = AudioSegment(
            audio_data_np.tobytes(),  # data
            frame_rate=self.sample_rate,  # sample rate
            sample_width=2,  # 16 bit
            channels=1  # mono
        )

        return audio_segment
    
class SileroRVC_TTS(TextToSpeech):
    def __init__(self, speaker=speaker, sample_rate=sample_rate_out, pitch_shift_semitones=4):
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.pitch_shift_semitones = pitch_shift_semitones

        self.model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language=language, speaker=model_id)
        self.model.to(device)

    @override
    def warmup(self) -> None:
        self.model.apply_tts('t', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('hi', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('nyako', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('test', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts(':D', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('pbpbpb', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('nyanya', speaker=speaker, sample_rate=sample_rate_out)
        self.model.apply_tts('!my~jouyonaofj845q985:JLKJ^%:LKj', speaker=speaker, sample_rate=sample_rate_out)

        rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_path='nyako/inference_temp/voice_conv.wav')
        rvc_convert(model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_path='nyako/inference_temp/voice_conv.wav')
    
    @override
    def generate_speech(self, text: str) -> AudioSegment | None:
        try:
            audio_tensor = self.model.apply_tts(text, speaker=self.speaker, sample_rate=self.sample_rate)
        except Exception as e:
            print("TTS failure. Error message: " + str(e) + "\n Input was: " + text)
            return

        # normalize
        audio_np = audio_tensor.numpy()
        audio_np = audio_np / audio_np.max()

        # bounce to wav
        with sf.SoundFile(FileIO('nyako/inference_temp/voice.wav', 'wb'), mode='w', samplerate=self.sample_rate, channels=1, format='wav', subtype='FLOAT') as f:
            f.write(audio_np)

        # convert with rvc
        rvc_convert(f0_up_key=4, resample_sr=sample_rate_out, model_path='nyako/rvc_voice_models/ayaka-jp_e101.pth', input_path='nyako/inference_temp/voice.wav', output_path='nyako/inference_temp/voice_conv.wav')

        with sf.SoundFile('nyako/inference_temp/voice_conv.wav', mode='r') as f:
            audio = f.read(dtype='float32')

        # TODO determine proper conversion for audio data

        audio_segment = AudioSegment(
            audio.tobytes(),
            sample_width=4,
            frame_rate= sample_rate_out,
            channels=1
        )

        return audio_segment