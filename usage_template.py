import qasync
import asyncio

import Transcribers
from TTS import MeloTTS

from event_system import EventBusSingleton
from event_system.events.System import StartupEvent, StartupStage
from event_system.events.Pipeline import MessageEvent, OutputRoutingEvent, UserInputEvent

from pipesys.core import AdminPanel, DiscordClientRunner
from pipesys.inputs import DiscordVoiceInput
from pipesys.processors import RealtimeMessageChunker, ConversationSessionProcessor
from pipesys.outputs import PipelineMonitor, FileLogger, DiscordVoiceOutput

from TaskManager import TaskManager

async def main():
    # region Core Modules

    ## MANDATORY Runs all async tasks, must be created before task-producing modules
    task_manager = TaskManager()

    ## Handles the discord client
    discord_client_runner = await DiscordClientRunner.create()

    admin_events = await AdminPanel.create(listen_to=OutputRoutingEvent)
    
    # endregion

    # region Input Modules

    ## Multi-user voice input via discord
    discord_voice_input = await DiscordVoiceInput.create(Transcribers.FasterWhisperTranscriber(), speech_timeout=0.3)
    
    input_monitor = await PipelineMonitor.create(listen_to=UserInputEvent)
    monitor = await PipelineMonitor.create(listen_to=MessageEvent)

    #speech_to_text = await pipesys.inputs.SpeechToTextInput.create(Transcribers.WhisperTranscriber())
    #console_input = await ConsoleInput.create(event_bus)
    #discord_input = await DiscordInput.create()
    
    # endregion

    # region Processing Modules

    ## The chunker accumulates messages over a time period and sends them to the next processor as a batch
    message_chunker = await RealtimeMessageChunker.create(listen_to=UserInputEvent, processor_delay=0.2)
    
    ## The conversation session processor queries the LLM
    conversation_session_processor = await ConversationSessionProcessor.create(listen_to=message_chunker)
    
    ## The message router sends the results to the output modules based on a tagging system
    ## For example, if the LLM produces an output with the string "[voice]", the message router will send the text after that tag to the voice output module
    #message_router = pipesys.processors.MessageRouter(listen_to=conversation_session_processor)

    # endregion

    # region Output Modules

    #console_output = await pipesys.outputs.ConsoleOutput.create(listen_to=conversation_session_processor)
    #speech_output = await TextToSpeechOutput.create(listen_to=conversation_session_processor)
    discord_voice_output = await DiscordVoiceOutput.create(listen_to=conversation_session_processor, text_to_speech=MeloTTS())

    message_logger = await FileLogger.create(listen_to=conversation_session_processor)

    #visual_output = await pipesys.outputs.VisualOutput.create(listen_to=conversation_session_processor, parent=admin_events)

    #discord_output = await DiscordOutput.create(listen_to=conversation_session_processor)

    # endregion

    print("warming up...")
    await EventBusSingleton.publish(StartupEvent(StartupStage.WARMUP))

    print("linking...")
    # extra linking

    print("running!")
    # run tasks
    await task_manager.run()

from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    # initialize pyqt5 event loop
    # this is necessary for compatibility between asyncio and pyqt5
    app = QApplication([])
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main())