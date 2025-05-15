import asyncio
from asyncio import AbstractEventLoop

import pyaudio

from event_system import EventBusSingleton
from event_system.events.Audio import (
    AudioDirection,
    AudioType,
    SpeakingStateUpdate,
    VolumeUpdatedEvent,
)
from event_system.events.Pipeline import SystemInputType, UserInputEvent
from event_system.events.System import CommandEvent, CommandType, TaskCreatedEvent
from pipesys import Pipe
from settings import INPUT_SAMPLING_RATE, FramesPerBuffer, debug_mode, speech_sensitivity_threshold
from Transcribers import Transcriber, WhisperTranscriber
from VAD_utils import detectVoiceActivity


class SpeechToTextInput(Pipe):
    asyncio_main_loop: AbstractEventLoop
    transcriber: Transcriber
    audio: pyaudio.PyAudio

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.noSpeechTime = 0
        self.speechRecordingTriggered = False
        self.speechBuffer: bytes = b""
        self.input_gain: float = 1.0
        self.stopped = False
        self.asyncio_main_loop = asyncio.get_event_loop()

    @classmethod
    async def create(cls, transcriber: Transcriber | None):
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

        if transcriber:
            self.transcriber = transcriber
        else:
            self.transcriber = WhisperTranscriber()

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.stop)
        EventBusSingleton.subscribe(
            VolumeUpdatedEvent(audio_type=AudioType.SYSTEM, audio_direction=AudioDirection.INPUT),
            self.on_input_volume_update,
        )

        task = asyncio.create_task(self.run())
        await EventBusSingleton.publish(TaskCreatedEvent(task, pretty_sender="Speech to Text"))
        return self

    def stop(self, event: CommandEvent):
        self.stream.stop_stream()
        self.stream.close()
        self.stopped = True

    # simple keepalive deal
    async def run(self):
        self.stream = self.audio.open(
            rate=INPUT_SAMPLING_RATE,
            channels=1,
            input=True,
            format=pyaudio.paFloat32,
            frames_per_buffer=FramesPerBuffer,
            stream_callback=self.microphone_input_callback,
        )
        while not self.stopped:
            await asyncio.sleep(0.1)

    async def on_input_volume_update(self, event: VolumeUpdatedEvent):
        if event.volume is None:
            return

        self.input_gain = event.volume

    async def mute(self):
        self.stream.stop_stream()

    async def unmute(self):
        self.stream.start_stream()

    def microphone_input_callback(self, in_data, frame_count, time_info, status):
        is_speaking_probability = detectVoiceActivity(in_data)

        if (
            is_speaking_probability > speech_sensitivity_threshold
            and not self.speechRecordingTriggered
        ):
            self.speechRecordingTriggered = True

            # raise user speaking state update event
            asyncio.run_coroutine_threadsafe(
                EventBusSingleton.publish(
                    SpeakingStateUpdate(True, AudioType.SYSTEM, AudioDirection.INPUT)
                ),
                self.asyncio_main_loop,
            )

        if self.speechRecordingTriggered:
            self.speechBuffer += in_data

        if is_speaking_probability < 0.5:
            self.noSpeechTime += 0.032
            if self.noSpeechTime > 1 and self.speechRecordingTriggered:
                # stop recording and reset no speech time
                self.speechRecordingTriggered = False
                self.noSpeechTime = 0

                # decode speech
                transcript = self.transcriber.transcribe_speech(
                    self.speechBuffer, input_gain=self.input_gain
                )

                if self.transcriber.supports_extra_tagging():
                    tags = self.transcriber.get_extra_tagging()
                    tags_string = ", ".join(tags)  # Convert the list of tags to a string
                    transcript = (
                        f"(Audio: {tags_string})" + transcript
                    )  # Prepend the tags to the transcript

                # raise user speaking state update event
                asyncio.run_coroutine_threadsafe(
                    EventBusSingleton.publish(
                        SpeakingStateUpdate(False, AudioType.SYSTEM, AudioDirection.INPUT)
                    ),
                    self.asyncio_main_loop,
                )

                # debug
                if debug_mode:
                    print("Transcript: " + transcript)

                # clear buffer after STT
                self.speechBuffer = b""

                # make sure text is not empty or only whitespace
                if not transcript.strip():
                    return (in_data, pyaudio.paContinue)

                # send transcript to next modules
                asyncio.run_coroutine_threadsafe(
                    EventBusSingleton.publish(
                        UserInputEvent(transcript, self, SystemInputType.VOICE, priority=2)
                    ),
                    self.asyncio_main_loop,
                )
        else:
            self.noSpeechTime = 0

        return (in_data, pyaudio.paContinue)
