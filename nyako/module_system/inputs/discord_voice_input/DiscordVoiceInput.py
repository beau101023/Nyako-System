import discord
from EventTopics import Topics
from EventBus import EventBus
import asyncio
from module_system.inputs.discord_voice_input.StreamSink import StreamSink
import torch

from nyako_vad import detectVoiceActivity
from nyako_stt import transcribeSpeech

from typing import Dict
from pydub import AudioSegment
from params import speech_sensitivity_threshold, debug_mode
import numpy as np
import io
from threading import Thread

class DiscordVoiceInput:
    stream_sink : StreamSink
    client : discord.Client
    speechRecordingTriggeredByUser : Dict[str, bool]
    speechBufferByUser : Dict[str, list[AudioSegment]]
    noSpeechTimeByUser : Dict[str, float]
    inputGain : float

    def __init__(self):
        pass

    @classmethod
    async def create(cls, event_bus: EventBus, client: discord.Client, publish_channel=Topics.Pipeline.USER_INPUT):
        self = DiscordVoiceInput()
        self.event_bus = event_bus
        self.publish_channel = publish_channel
        self.client = client
        self.voice_client: discord.VoiceClient = None
        self.stream_sink: StreamSink = StreamSink()

        self.noSpeechTimeByUser = {}
        self.speechRecordingTriggeredByUser = {}
        self.speechBufferByUser = {}
        self.inputGain = 1.0

        self.stopped = False

        # register event handlers
        client.event(self.on_ready)

        self.event_bus.subscribe(self.stop, Topics.System.STOP)
        self.event_bus.subscribe(self.onInputVolumeUpdate, Topics.Audio.INPUT_VOLUME_UPDATE)

        # create task
        self.task = asyncio.create_task(self.run())
        await self.event_bus.publish(Topics.System.TASK_CREATED, self.task)

        return self
    
    async def run(self):
        while not self.stopped:
            if self.stream_sink.has_data():
                
                ## Consume Audio
                # blocks until data is available, then returns the user id and audio segment
                user, audio_segment = self.stream_sink.pop_data()

                audio_segment = audio_segment.set_frame_rate(16000)
                audio_segment = audio_segment.set_channels(1)

                ## VAD
                audio_tensor = torch.from_numpy(np.array(audio_segment.get_array_of_samples(), np.float32))

                isSpeakingProbability = detectVoiceActivity(audio_tensor)

                if isSpeakingProbability > speech_sensitivity_threshold and not self.speechRecordingTriggeredByUser.get(user, False):
                    self.speechRecordingTriggeredByUser[user] = True

                    print("{0} started speaking".format(user))

                    # a user has started speaking
                    if not any(self.speechRecordingTriggeredByUser.values()):
                        # notify that user speech has started
                        await self.event_bus.publish(Topics.SpeechToText.USER_SPEAKING_STATE, Topics.SpeakingStateUpdate(starting=True))

                if self.speechRecordingTriggeredByUser.get(user, False):
                    # initialize speech buffer for user if it doesn't exist
                    if user not in self.speechBufferByUser:
                        self.speechBufferByUser[user] = []

                    self.speechBufferByUser[user].append(audio_segment)

                if isSpeakingProbability <= speech_sensitivity_threshold and self.speechRecordingTriggeredByUser.get(user, False):
                    if user not in self.noSpeechTimeByUser:
                        self.noSpeechTimeByUser[user] = 0

                    self.noSpeechTimeByUser[user] += 0.03

                    if self.noSpeechTimeByUser[user] >= 1:
                        self.speechRecordingTriggeredByUser[user] = False

                        print("{0} stopped speaking".format(user))

                        # all users have ceased speaking
                        if not any(self.speechRecordingTriggeredByUser.values()):
                            # notify that user speech has ended
                            await self.event_bus.publish(Topics.SpeechToText.USER_SPEAKING_STATE, Topics.SpeakingStateUpdate(ending=True))

                        speech_buffer = self.speechBufferByUser[user]

                        loop = asyncio.get_running_loop()
                        # the transcription method is blocking and slow so we run it in a separate thread
                        Thread(target=self.transcribeSpeechAndPublish, args=(speech_buffer, user, loop)).start()

                        # reset speech buffer
                        self.speechBufferByUser[user] = []

                        # reset no speech time
                        self.noSpeechTimeByUser[user] = 0

            else:
                # if there's no data, wait for 10 ms (audio chunk is 30 ms long)
                await asyncio.sleep(0.01)
                continue
        
        print("DiscordVoiceInput stopped")
        self.stream_sink.cleanup()
        self.__del__()

    # converts the audio segments to a single numpy array and transcribes it
    def transcribeSpeechAndPublish(self, speechBuffer, user, loop: asyncio.AbstractEventLoop):
        # Convert each AudioSegment to raw data and concatenate
        raw_data = b''.join(segment.raw_data for segment in speechBuffer)

        # Convert raw data to numpy array
        numpy_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)

        # transcribe speech
        transcribed_speech = transcribeSpeech(numpy_array, self.inputGain)

        if transcribed_speech == "" or transcribed_speech == None:
            return
        
        if debug_mode:
            print("[voice] {0}: {1}".format(user, transcribed_speech))
        
        # publish to pipeline
        coroutine = self.event_bus.publish(self.publish_channel, "[voice] {0}: {1}".format(user, transcribed_speech))
        asyncio.run_coroutine_threadsafe(coroutine, loop)


    def onInputVolumeUpdate(self, event: Topics.VolumeUpdate):
        self.input_gain = event.volume

    def stop(self):
        self.stopped = True

    # on bot ready
    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self.client))

        # connect to first available voice channel
        for channel in self.client.get_all_channels():
            if channel.type == discord.ChannelType.voice:
                self.voice_client: discord.VoiceClient = await channel.connect()
                self.stream_sink.set_voice_client(self.voice_client)

                # play sample to initialize the voice client
                sample = io.FileIO("nyako/audio/Basic 808 Kick_2.wav")
                discord_audio = discord.PCMAudio(sample)

                self.voice_client.play(discord_audio)
                
                self.voice_client.start_recording(sink=self.stream_sink, callback=self.recording_stopped_callback)
                break

    def recording_stopped_callback(self):
        pass

    def __del__(self):
        if self.voice_client != None:
            self.voice_client.stop_recording()
            self.voice_client.disconnect()
            self.voice_client = None