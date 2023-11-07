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

    await speech_output.whenSpeakingStarts(speech_to_text.mute)
    await speech_output.whenSpeakingEnds(speech_to_text.unmute)

    print("listening...")

    # await tasks
    await asyncio.gather(stt_task, chunker_task, emote_task)

    speech_to_text.stop()

asyncio.run(main())

async def test():
    speech_output = TextToSpeechOutput()

    speech_output.say("hello world")

#asyncio.run(test())