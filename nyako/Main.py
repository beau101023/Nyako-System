import asyncio
from PIL import Image

from module_system.inputs.ConsoleInput import ConsoleInput
from module_system.outputs.ConsoleOutput import ConsoleOutput
from module_system.outputs.VisualOutput import VisualOutput
from module_system.processors.ConversationSessionProcessor import ConversationSessionProcessor
from module_system.processors.RealtimeMessageChunker import RealtimeMessageChunker
from module_system.inputs.SpeechToTextInput import SpeechToTextInput
from module_system.outputs.TextToSpeechOutput import TextToSpeechOutput

import tkinter as tk

async def main():
    console_input = ConsoleInput()
    realtime_message_chunker = RealtimeMessageChunker()
    conversation_session_processor = ConversationSessionProcessor()
    console_output = ConsoleOutput()
    emote_output = VisualOutput()

    await console_input.link_to(realtime_message_chunker.priority_recieve)
    await realtime_message_chunker.link_to(conversation_session_processor.receive)
    await conversation_session_processor.link_to(console_output.receive)
    await conversation_session_processor.link_to(emote_output.receive)

    inputTask = await console_input.getTask()
    chunkTask = await realtime_message_chunker.getTask()
    emoteTask = await emote_output.getTask()

    await asyncio.gather(inputTask, chunkTask, emoteTask)

#asyncio.run(main())

async def test():
    # create modules
    speech_to_text = SpeechToTextInput()
    message_chunker = RealtimeMessageChunker()
    conversation_session_processor = ConversationSessionProcessor()
    speech_output = TextToSpeechOutput()
    visual_output = VisualOutput()

    print("warming up...")
    # warm up tts
    speech_output.warmup()

    print("getting tasks...")
    stt_task = await speech_to_text.getTask()
    chunker_task = await message_chunker.getTask()
    emote_task = await visual_output.getTask()

    print("linking...")
    # link modules
    await speech_to_text.link_to(message_chunker.receive)
    await message_chunker.link_to(conversation_session_processor.receive)
    await conversation_session_processor.link_to(speech_output.receive)
    await conversation_session_processor.link_to(visual_output.receive)

    print("listening...")

    # await tasks
    await asyncio.gather(stt_task, chunker_task, emote_task)

    speech_to_text.stop()

asyncio.run(test())