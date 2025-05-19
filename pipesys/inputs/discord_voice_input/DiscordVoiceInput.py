import asyncio
from threading import Thread

import discord
from pydub import AudioSegment

from event_system import EventBusSingleton
from event_system.events.Audio import (
    AudioDirection,
    AudioType,
    SpeakingStateUpdate,
    VolumeUpdatedEvent,
)
from event_system.events.Discord import (
    BotReadyEvent,
    VoiceChannelConnectedEvent,
    VoiceChannelDisconnectedEvent,
)
from event_system.events.Pipeline import SystemInputType, UserInputEvent
from event_system.events.System import CommandEvent, CommandType, TaskCreatedEvent
from pipesys import Pipe
from pipesys.inputs.discord_voice_input.StreamSink import StreamSink
from settings import debug_mode, speech_sensitivity_threshold
from Transcribers import Transcriber, WhisperTranscriber
from VAD_utils import detect_voice_activity


class DiscordVoiceInput(Pipe):
    """
    A Pipe that captures voice data from a Discord voice channel, detects speech,
    and transcribes the audio into text events for downstream processing.
    """

    def __init__(self, speech_timeout: float):
        """
        Initialize a DiscordVoiceInput instance.

        :param speech_timeout: The amount of silence (in seconds) required to consider speech ended.
        """
        self.voice_connection: discord.VoiceClient | None = None
        self.client: discord.Client | None = None
        self.stream_sink = StreamSink()

        self.no_speech_time_by_user: dict[int, float] = {}
        self.speech_recording_triggered_by_user: dict[int, bool] = {}
        self.speech_buffer_by_user: dict[int, list[AudioSegment]] = {}

        self.input_gain = 1.0
        self.speech_timeout = speech_timeout
        self.stopped = False

        # Default to WhisperTranscriber if none is provided in create().
        self.transcriber: Transcriber = WhisperTranscriber()

    @classmethod
    async def create(
        cls, transcriber: Transcriber | None, speech_timeout: float = 0.3
    ) -> "DiscordVoiceInput":
        """
        Factory method to create and launch the DiscordVoiceInput pipe as an async task.

        :param transcriber: A Transcriber instance (WhisperTranscriber by default).
        :param speech_timeout: The amount of silence (in seconds) required to consider speech ended.
        :return: An instance of DiscordVoiceInput.
        """
        instance = cls(speech_timeout)

        if transcriber:
            instance.transcriber = transcriber

        # Subscribe to relevant events
        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), instance.stop)
        EventBusSingleton.subscribe(
            VolumeUpdatedEvent(audio_type=AudioType.DISCORD, audio_direction=AudioDirection.INPUT),
            instance.on_input_volume_update,
        )

        EventBusSingleton.subscribe(VoiceChannelConnectedEvent, instance.on_voice_channel_connected)
        EventBusSingleton.subscribe(
            VoiceChannelDisconnectedEvent, instance.on_voice_channel_disconnected
        )
        EventBusSingleton.subscribe(BotReadyEvent, instance.on_bot_ready)

        # Create a long-running task for reading audio data
        task = asyncio.create_task(instance.run())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Discord Voice Input"))
        return instance

    async def run(self):
        """
        Main loop that polls audio data from the stream_sink and processes it.
        """
        while not self.stopped:
            if self.stream_sink.has_data() and self.voice_connection:
                data = self.stream_sink.pop_data()
                if data is not None:
                    user_id, audio_segment = data
                    await self._process_audio_chunk(user_id, audio_segment)
            else:
                # Sleep briefly to reduce CPU usage if no data is available
                await asyncio.sleep(0.01)

        print("DiscordVoiceInput stopped")
        await self._cleanup()

    async def _process_audio_chunk(self, user_id: int, audio_segment: AudioSegment):
        """
        Processes a chunk of audio for a given user:
        1. Detects if user is speaking via VAD.
        2. Handles transitions between speaking and silence.
        3. Buffers audio for transcription when speaking is detected.
        """
        # Detect speech
        is_speaking_probability = detect_voice_activity(audio_segment)

        # If the user transitions to speaking
        if (
            is_speaking_probability > speech_sensitivity_threshold
            and not self.speech_recording_triggered_by_user.get(user_id, False)
        ):
            await self._start_user_speaking(user_id)

        # If user is currently speaking, buffer the segment
        if self.speech_recording_triggered_by_user.get(user_id, False):
            self._append_to_speech_buffer(user_id, audio_segment)

        # If user transitions from speaking to silence
        if (
            is_speaking_probability <= speech_sensitivity_threshold
            and self.speech_recording_triggered_by_user.get(user_id, False)
        ):
            await self._handle_user_silence(user_id)

    async def _start_user_speaking(self, user_id: int):
        """
        Marks a user as speaking and sends a SpeakingStateUpdate event if this is the first user to speak.
        """
        if not any(self.speech_recording_triggered_by_user.values()):
            # If this is the first user to speak among all participants
            await EventBusSingleton.publish(
                SpeakingStateUpdate(True, AudioType.DISCORD, AudioDirection.INPUT)
            )

        self.speech_recording_triggered_by_user[user_id] = True
        print(f"User {user_id} started speaking")

    def _append_to_speech_buffer(self, user_id: int, audio_segment: AudioSegment):
        """
        Appends the latest audio segment to the user's speech buffer.
        """
        if user_id not in self.speech_buffer_by_user:
            self.speech_buffer_by_user[user_id] = []
        self.speech_buffer_by_user[user_id].append(audio_segment)

    async def _handle_user_silence(self, user_id: int):
        """
        Tracks silence duration. If it exceeds self.speech_timeout, mark user as no longer speaking and
        transcribe buffered audio.
        """
        self.no_speech_time_by_user[user_id] = self.no_speech_time_by_user.get(user_id, 0) + 0.03

        if self.no_speech_time_by_user[user_id] >= self.speech_timeout:
            self.speech_recording_triggered_by_user[user_id] = False
            print(f"User {user_id} stopped speaking")

            # Attempt to fetch the user display name
            user_name = str(user_id)
            if self.client:
                try:
                    discord_user: discord.User = await self.client.fetch_user(user_id)
                    if discord_user:
                        user_name = discord_user.display_name
                except (discord.NotFound, discord.HTTPException):
                    pass

            # Transcription in a separate thread since transcriber process may be both long and blocking
            speech_buffer = self.speech_buffer_by_user[user_id]
            self.speech_buffer_by_user[user_id] = []
            loop = asyncio.get_running_loop()
            Thread(
                target=self._transcribe_speech_and_publish,
                args=(speech_buffer, user_name, loop),
                daemon=True,
            ).start()

            self.no_speech_time_by_user[user_id] = 0

    def _transcribe_speech_and_publish(
        self, speech_buffer: list[AudioSegment], user_name: str, loop: asyncio.AbstractEventLoop
    ):
        """
        Concatenates all audio segments in the buffer, transcribes the audio, and publishes a UserInputEvent.
        Runs in a separate thread to avoid blocking the main async loop.
        """
        combined_audio = AudioSegment.empty()
        for segment in speech_buffer:
            combined_audio += segment

        transcription = self.transcriber.transcribe_speech(combined_audio, self.input_gain)
        if not transcription:
            return

        if debug_mode:
            print(f"[voice] {user_name}: {transcription}")

        # Publish the transcribed text as user input
        publish_coroutine = EventBusSingleton.publish(
            UserInputEvent(
                transcription, self, SystemInputType.DISCORD_VOICE, user_name=user_name, priority=2
            )
        )
        asyncio.run_coroutine_threadsafe(publish_coroutine, loop)

        # If no one else is speaking, send event indicating speech ended
        if not any(self.speech_recording_triggered_by_user.values()):
            end_speaking_coroutine = EventBusSingleton.publish(
                SpeakingStateUpdate(False, AudioType.DISCORD, AudioDirection.INPUT)
            )
            asyncio.run_coroutine_threadsafe(end_speaking_coroutine, loop)

    def on_input_volume_update(self, event: VolumeUpdatedEvent):
        """
        Event handler: Adjusts the voice input gain in response to a volume update event.
        """
        if event.volume:
            self.input_gain = event.volume
        else:
            self.input_gain = 1.0

    def stop(self, event: CommandEvent):
        """
        Event handler: Stops processing voice data when a STOP command is received.
        """
        self.stopped = True

    def on_bot_ready(self, event: BotReadyEvent):
        """
        Event handler: Sets the Discord client when the bot is ready.
        """
        self.client = event.client

    async def on_voice_channel_connected(self, event: VoiceChannelConnectedEvent):
        """
        Event handler: Starts recording when the bot successfully joins a voice channel.
        """
        self.voice_connection = event.voice_client

        # Play a startup sound
        # AFAIK, playing audio is required to initiate the voice connection and thus must come before recording
        with open("audio/startup.wav", "rb") as sample:
            self.voice_connection.play(discord.PCMAudio(sample))

        self.voice_connection.start_recording(
            sink=self.stream_sink,
            callback=lambda: None,  # Not currently doing anything when recording complete
        )

    def on_voice_channel_disconnected(self, event: VoiceChannelDisconnectedEvent):
        """
        Event handler: Stops recording and resets voice connection when bot leaves a voice channel.
        """
        if self.voice_connection:
            self.voice_connection.stop_recording()
            self.voice_connection = None

    async def _cleanup(self):
        """
        Cleanup method to disconnect from the voice channel if connected and turn off the stream sink buffering.
        """
        self.stream_sink.cleanup()
        if self.voice_connection:
            await self.voice_connection.disconnect()
            await EventBusSingleton.publish(VoiceChannelDisconnectedEvent())
