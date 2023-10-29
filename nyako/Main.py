import asyncio

from module_system.inputs.ConsoleInput import ConsoleInput
from module_system.outputs.ConsoleOutput import ConsoleOutput
from module_system.outputs.EmoteOutput import EmoteOutput
from module_system.processors.ConversationSessionProcessor import ConversationSessionProcessor
from module_system.processors.RealtimeMessageChunker import RealtimeMessageChunker

import tkinter as tk

async def main():
    # created in pipeline order
    console_input = ConsoleInput()
    realtime_message_chunker = RealtimeMessageChunker()
    conversation_session_processor = ConversationSessionProcessor()
    console_output = ConsoleOutput()

    await console_input.link_to(realtime_message_chunker)
    await realtime_message_chunker.link_to(conversation_session_processor)
    await conversation_session_processor.link_to(console_output)

    inputTask = await console_input.getTask()
    chunkTask = await realtime_message_chunker.getTask()

    await asyncio.gather(inputTask, chunkTask)

#asyncio.run(main())

async def test():
    console_input = ConsoleInput()
    realtime_message_chunker = RealtimeMessageChunker()
    conversation_session_processor = ConversationSessionProcessor()
    console_output = ConsoleOutput()

    window = tk.Tk()
    window.title("nyako")
    window.geometry("1000x1000")
    panel = tk.Label(window)
    img_path = "nyako/images/neutral.png"
    img = tk.PhotoImage(file=img_path)
    panel.configure(image=img)
    panel.image = img
    panel.pack(side="bottom", fill="both", expand="yes")

    emote_output = EmoteOutput(panel)

    await console_input.link_to(realtime_message_chunker.priority_recieve)
    await realtime_message_chunker.link_to(conversation_session_processor.receive)
    await conversation_session_processor.link_to(console_output.receive)
    await conversation_session_processor.link_to(emote_output.receive)

    inputTask = await console_input.getTask()
    chunkTask = await realtime_message_chunker.getTask()

    tkMainTask = asyncio.create_task(updateWindow(window))
    await asyncio.gather(inputTask, chunkTask, tkMainTask)

async def updateWindow(window):
    while True:
        window.update()
        await asyncio.sleep(0.1)

asyncio.run(test())