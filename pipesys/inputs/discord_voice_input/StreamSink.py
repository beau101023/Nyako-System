# thanks to https://github.com/ScruffyTheMoose for converting sinks for streaming
# https://github.com/ScruffyTheMoose/HushVC/blob/main/app/custom_core.py

from discord.sinks.core import Sink
from discord import VoiceClient
from pydub import AudioSegment
from queue import Queue
from typing import Dict


class StreamSink(Sink):
    # calls callback with every frame of audio data, along with the sender's user id
    def __init__(self, *, filters=None):
        super().__init__(filters=filters)
        self.encoding = "wav"

        # obj to store our super sweet awesome audio data
        self.byte_buffer: Dict[int, bytearray] = {}  # bytes
        # holds buffers of data for each user
        self.segment_buffer: Dict[int, Queue[AudioSegment]] = {}

        # audio data specifications
        self.sample_width = 2
        self.channels = 2
        self.sample_rate = 48000
        self.bytes_ps = 64000  # bytes added to buffer per second. automatically set in StreamSink.set_voice_client
        self.block_len = 0.032 * 3  # length in seconds * sample_rate/16000hz (downsampling ratio) * channels
        # min len to pull bytes from buffer
        self.buff_lim = int(self.bytes_ps * self.block_len)

        # var for tracking order of exported audio
        self.ct = 1

    def init(self, vc: VoiceClient):
        super().init(vc)

        if vc.decoder is None:
            return

        self.bytes_ps = vc.channel
        self.sample_rate = vc.decoder.SAMPLING_RATE
        self.channels = vc.decoder.CHANNELS
        self.sample_width = vc.decoder.SAMPLE_SIZE // vc.decoder.CHANNELS

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
                _ = self.segment_buffer[user].get()
                self.segment_buffer[user].put(audio_segment, timeout=0.05)

    def cleanup(self):
        self.finished = True

    def get_all_audio(self):
        raise NotImplementedError

    def get_user_audio(self, user):
        raise NotImplementedError

    def remove_user(self, user):
        if user in self.segment_buffer:
            del self.segment_buffer[user]

    def has_data(self) -> bool:
        return any(not queue.qsize() == 0 for queue in self.segment_buffer.values())

    def pop_data(self):
        for user, queue in self.segment_buffer.items():
            if not queue.qsize() == 0:
                return (user, queue.get())
        return None