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

    # region Core Modules

    ## The event bus is the central hub of the system.
    event_bus = EventBus()

    ## Collects all tasks, must be created before task-producing modules
    task_manager = TaskManager(event_bus)

    ## Handles automated waking of the system after periods of inactivity
    ## Can be triggered by raising Topics.System.SLEEP
    ##  and woken prematurely by raising Topics.System.WAKE
    sleep_manager = await SleepManager.create(event_bus)

    ## Control panel ui
    admin_events = await AdminEvents.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    
    # endregion

    # region Input Modules

    speech_to_text = await SpeechToTextInput.create(event_bus, publish_channel=Topics.Pipeline.USER_INPUT)
    #console_input = await ConsoleInput.create(event_bus)
    #discord_input = await DiscordInput.create(event_bus, publish_channel=Topics.Pipeline.USER_INPUT)
    
    # endregion

    # region Processing Modules

    ## The chunker accumulates messages over a time period and sends them to the next processor as a batch
    message_chunker = await RealtimeMessageChunker.create(event_bus, listen_topic=Topics.Pipeline.USER_INPUT, send_topic=Topics.Pipeline.CHUNKER)
    
    ## The conversation session processor queries the LLM
    conversation_session_processor = await ConversationSessionProcessor.create(event_bus, listen_topic=Topics.Pipeline.CHUNKER, send_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    
    ## The message router sends the results to the output modules based on a tagging system
    ## For example, if the LLM produces an output with the string "[voice]", the message router will send the text after that tag to the voice output module
    message_router = MessageRouter(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    # endregion

    # region Output Modules

    #console_output = await ConsoleOutput.create(event_bus)
    speech_output = await TextToSpeechOutput.create(event_bus, listen_topic=Topics.Router.VOICE)

    ## Provides a visual complement to other outputs
    ## Current implementation is a simple window that displays emotion images based on sentiment analysis of the conversation
    #visual_output = await VisualOutput.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY, master=admin_events.window)

    #discord_output = await DiscordOutput.create(event_bus, listen_topic=Topics.Router.DISCORD)

    ## Accepts textless commands from the LLM.
    ## TODO: make the command syntax more distinct and understandable.
    ##  LLM seems to have a hard time differentiating between commands and output tags.
    ## current commands:
    ##   - [sleep] - puts the system to sleep for one hour, during which it can be woken by any input but will not produce idle messages
    ##   - [listen] - does nothing. Allows the LLM to wait for further input.
    ##   - [shutdown] - stops the system.
    command_output = await CommandOutput.create(event_bus)

    # endregion

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