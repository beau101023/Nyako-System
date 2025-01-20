import discord

from event_system import EventBusSingleton

from event_system.events.Audio import AudioDirection, VolumeUpdatedEvent, AudioType, SpeakingStateUpdate
from event_system.events.System import TaskCreatedEvent, CommandEvent, CommandType
from event_system.events.Pipeline import UserInputEvent, SystemInputType
from event_system.events.Discord import BotReadyEvent, VoiceChannelConnectedEvent, VoiceChannelDisconnectedEvent

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
    speechRecordingTriggeredByUser : Dict[int, bool]
    speechBufferByUser : Dict[int, list[AudioSegment]]
    noSpeechTimeByUser : Dict[int, float]
    inputGain : float
    transcriber : Transcriber
    voice_connection: discord.VoiceClient | None

    def __init__(self, speech_timeout):
        self.voice_connection = None
        self.stream_sink = StreamSink()

        self.noSpeechTimeByUser = {}
        self.speechRecordingTriggeredByUser = {}
        self.speechBufferByUser = {}
        self.inputGain = 1.0
        self.speech_timeout = speech_timeout

        self.stopped = False

    @classmethod
    async def create(cls, transcriber: Transcriber | None, speech_timeout = 0.3) -> 'DiscordVoiceInput':
        self = DiscordVoiceInput(speech_timeout)

        if(transcriber):
            self.transcriber = transcriber
        else:
            self.transcriber = WhisperTranscriber()

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.stop)
        EventBusSingleton.subscribe(VolumeUpdatedEvent(None, AudioType.DISCORD, AudioDirection.INPUT), self.onInputVolumeUpdate)

        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, self.onVoiceChannelConnected)
        EventBusSingleton.subscribe(VoiceChannelDisconnectedEvent, self.onVoiceChannelDisconnected)

        EventBusSingleton.subscribe(BotReadyEvent, self.onBotReady)

        # create task
        task = asyncio.create_task(self.run())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Discord Voice Input"))

        return self
    
    async def run(self):
        while not self.stopped:
            if self.stream_sink.has_data() and self.voice_connection != None:
                
                ## Consume Audio
                # blocks until data is available, then returns the user id and audio segment
                data = self.stream_sink.pop_data()

                if(data is None):
                    continue

                user_id, audio_segment = data

                isSpeakingProbability = detectVoiceActivity(audio_segment)

                user_str = str(user_id)

                if isSpeakingProbability > speech_sensitivity_threshold and not self.speechRecordingTriggeredByUser.get(user_id, False):
                    # check if this is the first user to speak
                    if not any(self.speechRecordingTriggeredByUser.values()):
                        # if so, notify that user speech has started
                        await EventBusSingleton.publish(SpeakingStateUpdate(True, AudioType.DISCORD, AudioDirection.INPUT))
                        
                    self.speechRecordingTriggeredByUser[user_id] = True

                    print("{0} started speaking".format(user_str))

                if self.speechRecordingTriggeredByUser.get(user_id, False):
                    # initialize speech buffer for user if it doesn't exist
                    if user_id not in self.speechBufferByUser:
                        self.speechBufferByUser[user_id] = []

                    self.speechBufferByUser[user_id].append(audio_segment)

                if isSpeakingProbability <= speech_sensitivity_threshold and self.speechRecordingTriggeredByUser.get(user_id, False):
                    if user_id not in self.noSpeechTimeByUser:
                        self.noSpeechTimeByUser[user_id] = 0

                    self.noSpeechTimeByUser[user_id] += 0.03

                    if self.noSpeechTimeByUser[user_id] >= self.speech_timeout:
                        self.speechRecordingTriggeredByUser[user_id] = False

                        print("{0} stopped speaking".format(user_str))

                        # all users have ceased speaking
                        if not any(self.speechRecordingTriggeredByUser.values()):
                            # notify that user speech has ended
                            await EventBusSingleton.publish(SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.INPUT))

                        speech_buffer = self.speechBufferByUser[user_id]

                        if self.client:
                            try:
                                discord_user: discord.User = await self.client.fetch_user(user_id)
                                if discord_user:
                                    user_str = discord_user.display_name
                            except(discord.NotFound, discord.HTTPException):
                                pass

                        loop = asyncio.get_running_loop()
                        # the transcription method is blocking and slow so we run it in a separate thread
                        Thread(target=self.transcribeSpeechAndPublish, args=(speech_buffer, user_str, loop)).start()

                        # reset speech buffer
                        self.speechBufferByUser[user_id] = []

                        # reset no speech time
                        self.noSpeechTimeByUser[user_id] = 0

            else:
                # if there's no data, wait for 10 ms (audio chunk is 30 ms long)
                await asyncio.sleep(0.01)
                continue
        
        print("DiscordVoiceInput stopped")
        self.stream_sink.cleanup()
        await self.cleanup()

    # converts the audio segments to a single numpy array and transcribes it
    def transcribeSpeechAndPublish(self, speechBuffer: list[AudioSegment], user: str, loop: asyncio.AbstractEventLoop):
        # Concatenate all the AudioSegments
        combined = AudioSegment.empty()
        for segment in speechBuffer:
            combined += segment

        # transcribe speech
        transcribed_speech = self.transcriber.transcribeSpeech(combined, self.inputGain)

        if transcribed_speech == "" or transcribed_speech == None:
            return
        
        if debug_mode:
            print("[voice] {0}: {1}".format(user, transcribed_speech))


        # publish to pipeline
        coroutine = EventBusSingleton.publish(UserInputEvent(transcribed_speech, self, SystemInputType.DISCORD_VOICE, user_name=user, priority=2))
        asyncio.run_coroutine_threadsafe(coroutine, loop)


    def onInputVolumeUpdate(self, event: VolumeUpdatedEvent):
        self.input_gain = event.volume

    def stop(self, event: CommandEvent):
        self.stopped = True

    def onBotReady(self, event:BotReadyEvent):
        self.client = event.client

    async def onVoiceChannelConnected(self, event: VoiceChannelConnectedEvent):
        self.voice_connection = event.voice_client

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

    async def cleanup(self):
        if not self.voice_connection:
            return

        await self.voice_connection.disconnect()