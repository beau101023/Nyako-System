import re
from datetime import datetime

import settings
from settings import ASYNCOPENAI as CLIENT
from vectordb.RAG_utils import insertToMemory, retrieveMemoriesWithContext


async def get_response(messages: list, model=settings.chat_model):
    if messages is None:
        raise ValueError("messages cannot be None")

    response = await CLIENT.chat.completions.create(model=model, messages=messages)

    return response.choices[0].message.content


async def get_response_stream(messages: list, model=settings.chat_model):
    if messages is None:
        raise ValueError("messages cannot be None")

    async for response in await CLIENT.chat.completions.create(
        model=model, messages=messages, stream=True
    ):
        yield response.choices[0].delta.content


def format_message_as_dict(role: str, message: str) -> dict[str, str]:
    return {"role": role, "content": message}


def message_dict_to_string(message: dict[str, str]) -> str:
    return message["role"] + ": " + message["content"]


class ConversationSession:
    """
    A class to manage a conversation session.

    Attributes
    ----------
    systemP : dict
        A dictionary representing the system's prompt message.
    summarizeP : dict
        A dictionary representing the system's summarization prompt message.
    messages : list
        A list of messages exchanged during the conversation.
    memory : str
        A string representing the memory of the conversation.

    Methods
    -------
    query(message: str) -> str:
        Processes a user's message and returns the system's response.
    updateSystemPrompt(newPrompt: str):
        Updates the system's prompt message.
    mostRecentMessage() -> dict:
        Returns the most recent message in the conversation.
    getContext() -> list:
        Returns a formatted context ready to be fed into the LLM, including the system prompt, the long-term memory, the short-term memory, and the messages in the conversation.
    getLongTermMemory() -> dict:
        Returns a long-term memory chunk from the vector db.
    printFormattedMessageLog():
        Prints the formatted message log of the conversation.
    memorize(messages: list):
        Memorizes a list of messages.
    memorizeOldest():
        Memorizes and clears the oldest messages in the conversation.
    memorizeAll():
        Memorizes and clears all messages in the conversation.
    """

    def __init__(self, system_p=settings.chat_model_prompt, summarize_p=settings.summarize_prompt):
        self.systemP = format_message_as_dict("system", system_p)
        self.summarizeP = format_message_as_dict("system", summarize_p)
        self.current_context_messages: list[dict[str, str]] = []
        self.memory = {}

    async def stream_query(self, message: str, buffer_size: int):
        """
        Asynchronously streams a query message and processes response chunks.

        Args:
            message (str): The query message to be sent.
            buffer_size (int): The size of the buffer to accumulate response chunks before processing.

        Yields:
            str: Concatenated response chunks that are processed and stored.

        This function sends a query message, streams the response in chunks, and processes each chunk.
        It accumulates chunks in a buffer until a sentence-ending punctuation (., !, ?) is found or the buffer size limit is reached.
        The accumulated chunks are then concatenated, processed, stored, and yielded.
        """
        self._add_message_to_history(message)
        buffer = []
        buffer_length = 0
        async for response_chunk in get_response_stream(await self.get_context()):
            if response_chunk:
                buffer.append(response_chunk)
                buffer_length += len(response_chunk)
                if re.search(r"[.!?]", response_chunk) or (
                    buffer_length >= buffer_size and re.search(r"\s$", response_chunk)
                ):
                    concatenated_response = "".join(buffer)
                    yield concatenated_response
                    buffer = []
                    buffer_length = 0
        if buffer:
            concatenated_response = "".join(buffer)
            yield concatenated_response

    async def query(self, message: str) -> str:
        self._add_message_to_history(message)
        response = await get_response(await self.get_context())

        if not response:
            return ""

        return response

    def update_system_prompt(self, new_prompt: str):
        self.systemP = format_message_as_dict("system", new_prompt)

    def most_recent_message(self) -> dict:
        return self.current_context_messages[-1]

    async def get_context(self) -> list:
        context = [self.systemP]
        ltm = await self.get_long_term_memory()
        if ltm:
            context.append(ltm)
        if self.memory:
            context.append(self.memory)
        context += self.current_context_messages
        return context

    async def get_long_term_memory(self):
        memory_chunks = await retrieveMemoriesWithContext(
            self.most_recent_message()["content"],
            settings.ltm_retrieval_count,
            settings.ltm_context_size,
        )
        if len(memory_chunks) == 0:
            return None
        return self._format_memory_chunks(memory_chunks)

    async def memorize(self, messages):
        if messages is None or len(messages) == 0:
            return

        messages_string = "\n".join([message["content"] for message in messages])
        memory_management_input = [{"role": "user", "content": messages_string}]

        if self.memory != "":
            memory_management_input = [self.summarizeP] + [self.memory] + memory_management_input
        else:
            memory_management_input = [self.summarizeP] + memory_management_input

        memory_response = await get_response(memory_management_input, settings.summarization_model)

        if memory_response is None:
            return

        await insertToMemory(
            memory_response, "\n".join([message_dict_to_string(message) for message in messages])
        )
        self.memory = format_message_as_dict("user", "[short-term memory] " + memory_response)

    async def memorize_oldest(self, num_messages):
        oldest_messages = self.current_context_messages[:num_messages]
        await self.memorize(oldest_messages)
        self.current_context_messages = self.current_context_messages[num_messages:]

    async def memorize_all(self):
        await self.memorize(self.current_context_messages)
        self.current_context_messages = []

    def _add_message_to_history(self, message):
        time_string = datetime.now().strftime("%m/%d/%Y, %H:%M:%S ")
        self.current_context_messages.append(format_message_as_dict("user", time_string + message))

    async def add_llm_message_to_context(self, assistant_message: str) -> None:
        self.current_context_messages.append(format_message_as_dict("assistant", assistant_message))
        if (
            len(self.current_context_messages) > settings.max_context_len
            and settings.memorize_enabled
        ):
            await self.memorize_oldest(settings.num_messages_to_summarize)
        else:
            self.current_context_messages = self.current_context_messages[
                -settings.max_context_len :
            ]

    def _format_memory_chunks(self, memory_chunks):
        aggregate_text = "[long-term memory]\n"
        count = 0
        for chunk in memory_chunks:
            astext = "\n".join([message.origin_messages for message in chunk])
            aggregate_text += "MEMORY " + str(count) + ": " + astext + "\n"
            count += 1
        return format_message_as_dict("user", aggregate_text)
