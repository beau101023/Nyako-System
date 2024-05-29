import discord

from event_system import EventBusSingleton

from event_system.events.Audio import AudioDirection, VolumeUpdatedEvent, AudioType, SpeakingStateUpdate
from event_system.events.System import TaskCreatedEvent, CommandEvent, CommandType
from event_system.events.Pipeline import UserInputEvent, SystemInputType
from event_system.events.Discord import VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent

import asyncio
from pipesys import Pipe
from pipesys.inputs.discord_voice_input.StreamSink import StreamSink
import torch

from nyako_vad import detectVoiceActivity
from Transcribers import Transcriber
from Transcribers import WhisperTranscriber

from typing import Dict
from pydub import AudioSegment
from params import speech_sensitivity_threshold, debug_mode
import numpy as np
from threading import Thread

class DiscordVoiceInput(Pipe):
    stream_sink : StreamSink
    client : discord.Client | None = None
    speechRecordingTriggeredByUser : Dict[str, bool]
    speechBufferByUser : Dict[str, list[AudioSegment]]
    noSpeechTimeByUser : Dict[str, float]
    inputGain : float
    transcriber : Transcriber
    voice_connection: discord.VoiceClient | None

    def __init__(self):
        self.voice_client = None
        self.stream_sink = StreamSink()

        self.noSpeechTimeByUser = {}
        self.speechRecordingTriggeredByUser = {}
        self.speechBufferByUser = {}
        self.inputGain = 1.0

        self.stopped = False

    @classmethod
    async def create(cls, transcriber: Transcriber = WhisperTranscriber()) -> 'DiscordVoiceInput':
        self = DiscordVoiceInput()
        self.transcriber = transcriber

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.stop)
        EventBusSingleton.subscribe(VolumeUpdatedEvent(None, AudioType.DISCORD, AudioDirection.INPUT), self.onInputVolumeUpdate)

        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.onVoiceChannelConnected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.onVoiceChannelDisconnected)

        # create task
        task = asyncio.create_task(self.run())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Discord Voice Input"))

        return self
    
    async def run(self):
        while not self.stopped:
            if self.stream_sink.has_data() and self.voice_client != None:
                
                ## Consume Audio
                # blocks until data is available, then returns the user id and audio segment
                user, audio_segment = self.stream_sink.pop_data()

                audio_segment = audio_segment.set_frame_rate(16000)
                audio_segment = audio_segment.set_channels(1)

                ## format required by the VAD
                audio_tensor = torch.from_numpy(np.array(audio_segment.get_array_of_samples(), np.float32))

                isSpeakingProbability = detectVoiceActivity(audio_tensor)

                if isSpeakingProbability > speech_sensitivity_threshold and not self.speechRecordingTriggeredByUser.get(user, False):
                    self.speechRecordingTriggeredByUser[user] = True

                    print("{0} started speaking".format(user))

                    # check if this is the first user to speak
                    if not any(self.speechRecordingTriggeredByUser.values()):
                        # if so, notify that user speech has started
                        await EventBusSingleton.publish(SpeakingStateUpdate(True, AudioType.DISCORD, AudioDirection.INPUT))

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
                            await EventBusSingleton.publish(SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.INPUT))

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
    def transcribeSpeechAndPublish(self, speechBuffer: list[AudioSegment], user: str, loop: asyncio.AbstractEventLoop):
        # Convert each AudioSegment to raw data and concatenate
        raw_data = b''.join(segment.raw_data for segment in speechBuffer if segment.raw_data != None)

        # Convert raw data to numpy array
        numpy_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)

        # transcribe speech
        transcribed_speech = self.transcriber.transcribeSpeech(numpy_array, self.inputGain)

        if transcribed_speech == "" or transcribed_speech == None:
            return
        
        if debug_mode:
            print("[voice] {0}: {1}".format(user, transcribed_speech))
        
        # publish to pipeline
        coroutine = EventBusSingleton.publish(UserInputEvent(transcribed_speech, self, SystemInputType.DISCORD_VOICE, user_name=user))
        asyncio.run_coroutine_threadsafe(coroutine, loop)


    def onInputVolumeUpdate(self, event: VolumeUpdatedEvent):
        self.input_gain = event.volume

    def stop(self, event: CommandEvent):
        self.stopped = True

    def onVoiceChannelConnected(self, event: VoiceChannelConnectedEvent):
        self.voice_connection = event.voice_client
        self.stream_sink.set_voice_client(event.voice_client)

        # play sample to initialize the voice client
        sample = open("nyako/audio/Basic 808 Kick_2.wav", 'rb')
        self.voice_connection.play(discord.PCMAudio(sample))

        self.voice_connection.start_recording(sink=self.stream_sink, callback=self.recording_stopped_callback)

    def onVoiceChannelDisconnected(self, event: VoiceChannelDisconnectedEvent):
        if self.voice_connection == None:
            return

        self.voice_connection.stop_recording()
        self.voice_connection = None

    def recording_stopped_callback(self):
        pass

    def __del__(self):
        if self.voice_client != None:
            self.voice_client.stop_recording()
            self.voice_client.disconnect()
            self.voice_client = None