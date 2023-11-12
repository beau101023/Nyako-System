import asyncio

from module_system.inputs.ConsoleInput import ConsoleInput
from module_system.outputs.ConsoleOutput import ConsoleOutput
from module_system.outputs.VisualOutput import VisualOutput
from module_system.processors.ConversationSessionProcessor import ConversationSessionProcessor
from module_system.processors.RealtimeMessageChunker import RealtimeMessageChunker
from module_system.inputs.SpeechToTextInput import SpeechToTextInput
from module_system.outputs.TextToSpeechOutput import TextToSpeechOutput
from module_system.processors.MessageRouter import MessageRouter
from AdminEvents import AdminEvents
from TaskManager import TaskManager

from EventBus import EventBus
from EventTopics import Topics

async def main():

    event_bus = EventBus()

    # collects all tasks, must be created before task-producing modules
    task_manager = TaskManager(event_bus)

    # for events triggered by the admin running the bot
    # eventually this'll be a control panel ui of some sort
    admin_events = AdminEvents(event_bus)

    # create modules. These are accessed, despite what pylance says
    #speech_to_text = await SpeechToTextInput.create(event_bus)
    console_input = await ConsoleInput.create(event_bus)

    message_chunker = await RealtimeMessageChunker.create(event_bus)
    conversation_session_processor = await ConversationSessionProcessor.create(event_bus)
    message_router = MessageRouter(event_bus)

    speech_output = await TextToSpeechOutput.create(event_bus)
    visual_output = VisualOutput(event_bus)

    print("warming up...")
    event_bus.publish(Topics.System.PRE_LINKING)

    print("linking...")
    # link modules
    event_bus.subscribe(message_chunker.onMessage, Topics.Pipeline.CONSOLE_IN)
    
    event_bus.subscribe(conversation_session_processor.onMessage, Topics.Pipeline.CHUNKER)

    event_bus.subscribe(visual_output.onMessage, Topics.Pipeline.CONVERSATION_SESSION_REPLY)
    event_bus.subscribe(message_router.onMessage, Topics.Pipeline.CONVERSATION_SESSION_REPLY)

    event_bus.subscribe(speech_output.onMessage, Topics.Router.VOICE)

    print("running!")

    # run tasks
    await task_manager.run()

    # stop tasks
    event_bus.publish(Topics.System.STOP)

asyncio.run(main())

async def test():
    pass

#asyncio.run(test())