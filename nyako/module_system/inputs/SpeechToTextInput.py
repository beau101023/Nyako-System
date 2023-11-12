import asyncio
import pyaudio
from nyako_stt import transcribeSpeech
from nyako_vad import detectVoiceActivity
import torch
from params import FramesPerBuffer, INPUT_SAMPLING_RATE

from EventTopics import Topics

torch.set_num_threads(3)

class SpeechToTextInput:
    @classmethod
    async def create(cls, event_bus):
        self = SpeechToTextInput()
        self.event_bus = event_bus
        self.event_bus.subscribe(self.stop, Topics.System.STOP)
        self.event_bus.subscribe(self.onSpeakingStateUpdate, Topics.TTS.SPEAKING_STATE)

        self.audio = pyaudio.PyAudio()
        self.noSpeechTime = 0
        self.speechRecordingTriggered = False
        self.speechBuffer = bytes()

        self.task = asyncio.create_task(self.run())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
        return self
        
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()

    async def run(self):
        self.stream = self.audio.open(rate=INPUT_SAMPLING_RATE, channels=1, input=True, format=pyaudio.paFloat32, frames_per_buffer=FramesPerBuffer, stream_callback=self.microphoneInputCallback)
        while True:
            await asyncio.sleep(0.1)
    
    async def onSpeakingStateUpdate(self, event: Topics.SpeakingStateUpdate):
        if event.starting:
            await self.mute()
        elif event.ending:
            await self.unmute()

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
                asyncio.run(self.event_bus.publish(Topics.Pipeline.SPEECH_TO_TEXT_IN, "[voice] beau: " + transcript))
        else:
            self.noSpeechTime = 0

        return (in_data, pyaudio.paContinue)