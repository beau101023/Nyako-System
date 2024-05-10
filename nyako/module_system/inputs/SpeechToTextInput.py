import asyncio
import pyaudio
import nyako_stt
from nyako_vad import detectVoiceActivity
from params import FramesPerBuffer, INPUT_SAMPLING_RATE, debug_mode, speech_sensitivity_threshold

from EventTopics import Topics

class SpeechToTextInput:
    transcriber: nyako_stt.Transcriber

    @classmethod
    async def create(
        cls, event_bus,
        transcriber: nyako_stt.Transcriber=nyako_stt.WhisperTranscriber(),
        publish_channel=Topics.Pipeline.USER_INPUT
        ):
        self = SpeechToTextInput()

        self.transcriber = transcriber

        self.event_bus = event_bus
        self.event_bus.subscribe(self.stop, Topics.System.STOP)
        self.event_bus.subscribe(self.onSpeakingStateUpdate, Topics.TTS.SPEAKING_STATE)
        self.event_bus.subscribe(self.onInputVolumeUpdate, Topics.Audio.INPUT_VOLUME_UPDATE)

        self.publish_to = publish_channel

        self.audio: pyaudio.PyAudio = pyaudio.PyAudio()
        self.noSpeechTime = 0
        self.speechRecordingTriggered = False
        self.speechBuffer = bytes()
        self.input_gain = 1.0
        self.stopped = False

        self.task = asyncio.create_task(self.run())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)
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
    
    async def onSpeakingStateUpdate(self, event: Topics.SpeakingStateUpdate):
        if event.starting:
            await self.mute()
        elif event.ending:
            await self.unmute()

    async def onInputVolumeUpdate(self, event: Topics.VolumeUpdate):
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
            asyncio.ensure_future(self.event_bus.publish(Topics.SpeechToText.USER_SPEAKING_STATE, Topics.SpeakingStateUpdate(starting=True)))

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
                asyncio.ensure_future(self.event_bus.publish(Topics.SpeechToText.USER_SPEAKING_STATE, Topics.SpeakingStateUpdate(ending=True)))

                # debug
                if debug_mode:
                    print("Transcript: " + transcript)

                # clear buffer after STT
                self.speechBuffer = bytes()

                # make sure text is not empty
                if transcript == "":
                    return (in_data, pyaudio.paContinue)

                # send transcript to next modules
                asyncio.ensure_future(self.event_bus.publish(self.publish_to, "[voice] beau: " + transcript))
        else:
            self.noSpeechTime = 0

        return (in_data, pyaudio.paContinue)