import asyncio
from module_system.core.producer import Producer
import pyaudio
from nyako_stt import transcribeSpeech
from nyako_vad import detectVoiceActivity
import torch
from params import FramesPerBuffer, INPUT_SAMPLING_RATE

class SpeechToTextInput(Producer):
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.noSpeechTime = 0
        self.speechRecordingTriggered = False
        self.speechBuffer = bytes()
        torch.set_num_threads(3)
        
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()

    async def run(self):
        self.stream = self.audio.open(rate=INPUT_SAMPLING_RATE, channels=1, input=True, format=pyaudio.paFloat32, frames_per_buffer=FramesPerBuffer, stream_callback=self.microphoneInputCallback)
        while True:
            await asyncio.sleep(0.1)

    async def getTask(self):
        task = asyncio.create_task(self.run())
        return task
    
    async def mute(self):
        self.stream.stop_stream()

    async def unmute(self):
        self.stream.start_stream()

    def microphoneInputCallback(self, in_data, frame_count, time_info, status):
        isSpeakingProbability = detectVoiceActivity(in_data)

        if isSpeakingProbability > 0.5 and not self.speechRecordingTriggered:
            self.speechRecordingTriggered = True

        if self.speechRecordingTriggered:
            self.speechBuffer += in_data

        if isSpeakingProbability < 0.5:
            self.noSpeechTime += 0.032
            if self.noSpeechTime > 1 and self.speechRecordingTriggered:

                # stop recording and reset no speech time
                self.speechRecordingTriggered = False
                self.noSpeechTime = 0

                # decode speech
                transcript = transcribeSpeech(self.speechBuffer)

                # debug
                print("Transcript: " + transcript)

                # clear buffer after STT
                self.speechBuffer = bytes()

                # make sure text is not empty
                if transcript == "":
                    return (in_data, pyaudio.paContinue)

                # send transcript to next modules
                asyncio.run(self.send(transcript))
        else:
            self.noSpeechTime = 0

        return (in_data, pyaudio.paContinue)