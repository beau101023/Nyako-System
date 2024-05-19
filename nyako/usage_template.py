import torch
torch.set_num_threads(3)

import Transcribers

import asyncio

import module_system

### NOTE: You need to run VSCode as administrator for this specific import to work due to stupid shit with TextToSpeechOutput's innerworkings
###     as such, it's not imported by default when you import module_system
from module_system.outputs.TextToSpeechOutput import TextToSpeechOutput

from AdminEvents import AdminEvents
from TaskManager import TaskManager

from EventBus import EventBus
from EventTopics import Topics

async def main():
    # region Core Modules

    ## MANDATORY The event bus is the central hub of the system.
    event_bus = EventBus()

    ## MANDATORY Collects all tasks, must be created before task-producing modules
    task_manager = TaskManager(event_bus)

    ## Handles the discord client
    #discord_client_runner = await DiscordClientRunner.create(event_bus)
    #discord_client = discord_client_runner.getClient()

    ## Handles automated waking of the system after periods of inactivity
    ## Can be triggered by raising Topics.System.SLEEP
    ##  and woken prematurely by raising Topics.System.WAKE
    #sleep_manager = await SleepManager.create(event_bus)

    ## Control panel ui
    admin_events = await AdminEvents.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    
    # endregion

    # region Input Modules

    ## Multi-user voice input via discord
    ## Joins the first voice channel available to the discord client
    #discord_voice_input = await DiscordVoiceInput.create(event_bus, discord_client, publish_channel=Topics.Pipeline.USER_INPUT)
    
    speech_to_text = await module_system.inputs.SpeechToTextInput.create(event_bus, transcriber=Transcribers.WhisperTranscriber(no_speech_probability_threshold=1.0), publish_channel=Topics.Pipeline.USER_INPUT)
    #console_input = await ConsoleInput.create(event_bus)
    #discord_input = await DiscordInput.create(event_bus, discord_client, publish_channel=Topics.Pipeline.USER_INPUT)
    
    # endregion

    # region Processing Modules

    ## The chunker accumulates messages over a time period and sends them to the next processor as a batch
    message_chunker = await module_system.processors.RealtimeMessageChunker.create(event_bus, listen_topic=Topics.Pipeline.USER_INPUT, send_topic=Topics.Pipeline.CHUNKER)
    
    ## The conversation session processor queries the LLM
    conversation_session_processor = await module_system.processors.ConversationSessionProcessor.create(event_bus, listen_topic=Topics.Pipeline.CHUNKER, send_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    
    ## The message router sends the results to the output modules based on a tagging system
    ## For example, if the LLM produces an output with the string "[voice]", the message router will send the text after that tag to the voice output module
    #message_router = MessageRouter(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    # endregion

    # region Output Modules

    console_output = await module_system.outputs.ConsoleOutput.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    speech_output = await TextToSpeechOutput.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    user_input_monitor = await module_system.outputs.ConsoleOutput.create(event_bus, listen_topic=Topics.Pipeline.CHUNKER)


    visual_output = await module_system.outputs.VisualOutput.create(event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY, master=admin_events.window)

    #discord_output = await DiscordOutput.create(event_bus, discord_client, listen_topic=Topics.Router.DISCORD)

    #command_output = await module_system.outputs.CommandOutput.create(event_bus)

    # endregion

    print("warming up...")
    await event_bus.publish(Topics.System.WARMUP)

    print("linking...")
    # extra linking

    print("running!")

    # run tasks
    await task_manager.run()

asyncio.run(main())