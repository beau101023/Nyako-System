import asyncio
from processors.ConversationSessionProcessor import ConversationSessionProcessor
from processors.RealtimeMessageChunker import RealtimeMessageChunker
from inputs.ConsoleInput import ConsoleInput
from outputs.ConsoleOutput import ConsoleOutput

async def main():
    # created in pipeline order
    console_input = ConsoleInput()
    realtime_message_chunker = RealtimeMessageChunker()
    conversation_session_processor = ConversationSessionProcessor()
    console_output = ConsoleOutput()

    await console_input.add_listener(realtime_message_chunker)
    await realtime_message_chunker.add_listener(conversation_session_processor)
    await conversation_session_processor.add_listener(console_output)

    inputTask = await console_input.start()
    chunkTask = await realtime_message_chunker.start()

    await asyncio.gather(inputTask, chunkTask)

#asyncio.run(main())

async def test():
    console_input = ConsoleInput()
    realtime_message_chunker = RealtimeMessageChunker()
    console_output = ConsoleOutput()

    await console_input.add_listener(realtime_message_chunker)
    await realtime_message_chunker.add_listener(console_output)

    inputTask = await console_input.start()
    chunkTask = await realtime_message_chunker.start()

    await asyncio.gather(inputTask, chunkTask)

asyncio.run(test())