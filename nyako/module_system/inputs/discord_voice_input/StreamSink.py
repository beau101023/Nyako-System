# thanks to https://github.com/ScruffyTheMoose for converting sinks for streaming
# https://github.com/ScruffyTheMoose/HushVC/blob/main/app/custom_core.py

from discord.sinks.core import Filters, Sink, default_filters
from discord import VoiceClient
from pydub import AudioSegment
from queue import Queue
from typing import Dict


class StreamSink(Sink):
    # calls callback with every frame of audio data, along with the sender's user id
    def __init__(self, *, filters=None):
        if filters is None:
            filters = default_filters
        self.filters = filters
        Filters.__init__(self, **self.filters)
        self.vc = None
        self.audio_data = {}

        # obj to store our super sweet awesome audio data
        self.buffer = StreamBuffer()

    def write(self, data, user):
        # we overload the write method to take advantage of the already running thread for recording
        self.buffer.write(data=data, user=user)

    def cleanup(self):
        self.finished = True

    def get_all_audio(self):
        # not applicable for streaming but may cause errors if not overloaded
        pass

    def get_user_audio(self, user):
        # not applicable for streaming but will def cause errors if not overloaded called
        pass

    def set_voice_client(self, vc: VoiceClient):
        self.vc = vc
        self.buffer.bytes_ps = vc.channel.bitrate

    def remove_user(self, user):
        self.buffer.remove_user(user)

    def has_data(self) -> bool:
        audio_buffer = self.buffer.segment_buffer
        if audio_buffer == {}:
            return False
        
        # if any of the queues aren't empty, return true
        has_data = [not audio_buffer[user].empty() for user in audio_buffer].count(True) > 0
        return has_data
    
    def pop_data(self) -> tuple[str, AudioSegment]:

        audio_buffer = self.buffer.segment_buffer

        assert isinstance(audio_buffer, dict)

        if audio_buffer == {}:
            return None, None

        # getting the first user with data in their queue
        user = [user for user in audio_buffer if not audio_buffer[user].empty()][0]

        # getting the first audio segment from the user's queue
        audio_segment = audio_buffer[user].get()

        # returning the user id and audio segment
        return user, audio_segment


class StreamBuffer:
    def __init__(self) -> None:
        # holds byte-form audio data as it builds
        self.byte_buffer: Dict[str, bytearray] = {}  # bytes

        # holds buffers of data for each user
        self.segment_buffer: Dict[str, Queue[AudioSegment]] = {}

        # audio data specifications
        self.sample_width = 2
        self.channels = 2
        self.sample_rate = 48000
        self.bytes_ps = 64000  # bytes added to buffer per second. automatically set in StreamSink.set_voice_client
        self.block_len = 0.032 * 3 * 2  # length in seconds * sample_rate/16000hz (downsampling ratio) * channels
        # min len to pull bytes from buffer
        self.buff_lim = int(self.bytes_ps * self.block_len)

        # var for tracking order of exported audio
        self.ct = 1

    # method for adding data to the buffer
    def write(self, data, user) -> None:

        # creating byte buffer for user if it doesn't exist
        if user not in self.byte_buffer:
            self.byte_buffer[user] = bytearray()

        self.byte_buffer[user] += data  # data is a bytearray object
        # checking amount of data in the buffer
        if len(self.byte_buffer[user]) > self.buff_lim:

            # grabbing slice from the buffer to work with
            byte_slice = self.byte_buffer[user][:self.buff_lim]

            # creating AudioSegment object with the slice
            audio_segment = AudioSegment(data=byte_slice,
                                         sample_width=self.sample_width,
                                         frame_rate=self.sample_rate,
                                         channels=self.channels,
                                         )

            # removing the old stinky trash data from buffer - ew get it out of there already
            self.byte_buffer[user] = self.byte_buffer[user][self.buff_lim:]
            # ok much better now

            # creating queue for user if it doesn't exist
            if user not in self.segment_buffer:
                self.segment_buffer[user] = Queue(maxsize=32)

            try:
                # adding AudioSegment to the user's queue
                self.segment_buffer[user].put(audio_segment, timeout=0.05)
            except:
                # if the queue is full, we'll consume a segment ourselves and then insert the new one
                #  we consume and insert rather than dropping the new segment because we want to
                #  ensure we aren't reacting to audio that is too old
                self.segment_buffer[user].get()
                self.segment_buffer[user].put(audio_segment, timeout=0.05)
                pass
    
    def remove_user(self, user) -> None:
        if user in self.segment_buffer:
            del self.segment_buffer[user]