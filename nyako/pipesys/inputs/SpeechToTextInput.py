import asyncio
import pyaudio
from Transcribers import Transcriber, WhisperTranscriber
from nyako_vad import detectVoiceActivity
from params import FramesPerBuffer, INPUT_SAMPLING_RATE, debug_mode, speech_sensitivity_threshold

from EventBus import EventBus

from asyncio import AbstractEventLoop

from nyako.events.IO import SystemInputType, UserInputEvent
from events.System import CommandEvent, CommandType, TaskCreatedEvent
from events.Audio import VolumeUpdatedEvent, AudioType, SpeakingStateUpdate

class SpeechToTextInput:
    asyncio_main_loop: AbstractEventLoop
    transcriber: Transcriber
    event_bus: EventBus
    audio: pyaudio.PyAudio

    @classmethod
    async def create(cls, event_bus: EventBus, transcriber: Transcriber= WhisperTranscriber()):
        """
        Creates an instance of the SpeechToTextInput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        transcriber (nyako_stt.Transcriber): the transcriber to use
        publish_channel (str): the channel

        Returns:
        SpeechToTextInput: the created instance
        """
        self = SpeechToTextInput()

        self.asyncio_main_loop = asyncio.get_event_loop()
        self.transcriber = transcriber

        self.event_bus = event_bus
        self.event_bus.subscribe(CommandEvent(CommandType.STOP), self.stop)
        self.event_bus.subscribe(VolumeUpdatedEvent(None, AudioType.SYSTEM_IN), self.onInputVolumeUpdate)

        self.audio = pyaudio.PyAudio()
        self.noSpeechTime = 0
        self.speechRecordingTriggered = False
        self.speechBuffer = bytes()
        self.input_gain = 1.0
        self.stopped = False

        task = asyncio.create_task(self.run())
        await self.event_bus.publish(TaskCreatedEvent(task))
        return self
        
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.stopped = True
    
    # simple keepalive deal
    async def run(self):
        self.stream = self.audio.open(rate=INPUT_SAMPLING_RATE, channels=1, input=True, format=pyaudio.paFloat32, frames_per_buffer=FramesPerBuffer, stream_callback=self.microphoneInputCallback)
        while not self.stopped:
            await asyncio.sleep(0.1)

    async def onInputVolumeUpdate(self, event: VolumeUpdatedEvent):
        self.input_gain = event.volume

    async def mute(self):
        self.stream.stop_stream()

    async def unmute(self):
        self.stream.start_stream()

    def microphoneInputCallback(self, in_data, frame_count, time_info, status):
        isSpeakingProbability = detectVoiceActivity(in_data)

        if isSpeakingProbability > speech_sensitivity_threshold and not self.speechRecordingTriggered:
            self.speechRecordingTriggered = True

            # raise user speaking state update event
            asyncio.run_coroutine_threadsafe(
                self.event_bus.publish(SpeakingStateUpdate(True, AudioType.SYSTEM_IN)),
                self.asyncio_main_loop)

        if self.speechRecordingTriggered:
            self.speechBuffer += in_data

        if isSpeakingProbability < 0.5:
            self.noSpeechTime += 0.032
            if self.noSpeechTime > 1 and self.speechRecordingTriggered:

                # stop recording and reset no speech time
                self.speechRecordingTriggered = False
                self.noSpeechTime = 0

                # decode speech
                transcript = self.transcriber.transcribeSpeech(self.speechBuffer, input_gain=self.input_gain)
                
                if(self.transcriber.supports_extra_tagging()):
                    tags = self.transcriber.get_extra_tagging()
                    tags_string = ", ".join(tags)  # Convert the list of tags to a string
                    transcript = f"(Audio: {tags_string})" + transcript  # Prepend the tags to the transcript

                # raise user speaking state update event
                asyncio.run_coroutine_threadsafe(
                    self.event_bus.publish(SpeakingStateUpdate(False, AudioType.SYSTEM_IN)),
                    self.asyncio_main_loop)

                # debug
                if debug_mode:
                    print("Transcript: " + transcript)

                # clear buffer after STT
                self.speechBuffer = bytes()

                # make sure text is not empty or only whitespace
                if not transcript.strip():
                    return (in_data, pyaudio.paContinue)

                # send transcript to next modules
                asyncio.run_coroutine_threadsafe(
                    self.event_bus.publish(UserInputEvent(transcript, SystemInputType.VOICE)),
                    self.asyncio_main_loop)
        else:
            self.noSpeechTime = 0

        return (in_data, pyaudio.paContinue)