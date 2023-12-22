import torch
torch.set_num_threads(3)

import asyncio
import discord

from module_system.inputs.ConsoleInput import ConsoleInput
from module_system.inputs.DiscordInput import DiscordInput
from module_system.outputs.DiscordOutput import DiscordOutput
from module_system.outputs.ConsoleOutput import ConsoleOutput
from module_system.outputs.VisualOutput import VisualOutput
from module_system.processors.ConversationSessionProcessor import ConversationSessionProcessor
from module_system.processors.RealtimeMessageChunker import RealtimeMessageChunker
from module_system.inputs.SpeechToTextInput import SpeechToTextInput
from module_system.outputs.TextToSpeechOutput import TextToSpeechOutput
from module_system.processors.MessageRouter import MessageRouter
from module_system.outputs.CommandOutput import CommandOutput
from AdminEvents import AdminEvents
from TaskManager import TaskManager
from module_system.core.SleepManager import SleepManager

from EventBus import EventBus
from EventTopics import Topics

from params import DISCORD_BOT_TOKEN

async def main():

    event_bus = EventBus()

    # collects all tasks, must be created before task-producing modules
    task_manager = TaskManager(event_bus)

    sleep_manager = await SleepManager.create(event_bus)

    # for events triggered by the admin running the bot
    # eventually this'll be a control panel ui of some sort
    admin_events = await AdminEvents.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    # create modules. These are accessed, despite what pylance says
    speech_to_text = await SpeechToTextInput.create(event_bus, publish_channel=Topics.Pipeline.USER_INPUT)
    #console_input = await ConsoleInput.create(event_bus)
    #discord_input = await DiscordInput.create(event_bus, publish_channel=Topics.Pipeline.USER_INPUT)

    message_chunker = await RealtimeMessageChunker.create(event_bus, listen_topic=Topics.Pipeline.USER_INPUT, send_topic=Topics.Pipeline.CHUNKER)
    conversation_session_processor = await ConversationSessionProcessor.create(event_bus, listen_topic=Topics.Pipeline.CHUNKER, send_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    message_router = MessageRouter(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    #console_output = await ConsoleOutput.create(event_bus)
    speech_output = await TextToSpeechOutput.create(event_bus, listen_topic=Topics.Router.VOICE)
    #visual_output = await VisualOutput.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY, master=admin_events.window)
    #discord_output = await DiscordOutput.create(event_bus, listen_topic=Topics.Router.DISCORD)

    # enables textless commands like [listening], [sleep]
    command_output = await CommandOutput.create(event_bus)

    print("warming up...")
    await event_bus.publish(Topics.System.WARMUP)

    print("linking...")
    # extra linking

    print("running!")

    # run tasks
    await task_manager.run()

asyncio.run(main())

async def test():
    pass

#asyncio.run(test())