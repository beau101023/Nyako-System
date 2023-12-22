import discord
from EventBus import EventBus
from EventTopics import Topics

class DiscordOutput:
    def __init__(self, event_bus: EventBus, recieve_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY):
        self.event_bus = event_bus
        self.recieve_topic = recieve_topic
        self.listeningChannel = None

    @classmethod
    async def create(cls, event_bus: EventBus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY):
        self = DiscordOutput(event_bus, recieve_topic=listen_topic)
        self.event_bus.subscribe(self.set_channel, Topics.Discord.LISTENING_CHANNEL_SET)
        self.event_bus.subscribe(self.send_message, self.recieve_topic)

        await self.event_bus.publish(Topics.System.OUTPUT_STATE, Topics.OutputStateUpdate("discord", True))
        return self

    def set_channel(self, channel: discord.TextChannel):
        self.listeningChannel = channel

    async def send_message(self, message: str):
        # discord will throw an error if the message is empty
        if message is None or message == "":
            return

        if self.listeningChannel is not None:
            await self.listeningChannel.send(message)