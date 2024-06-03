from datetime import datetime

import params
from params import CLIENT_INSTANCE as client

from vectordb.nyako_ltm import insertToMemory
from vectordb.nyako_ltm import retrieveMemoriesWithContext


def get_response(messages, model=params.chat_model):

    if messages == None:
        raise ValueError("messages cannot be None")

    response = client.chat.completions.create(

        model = model,

        messages = messages

    )

    return response.choices[0].message.content


def format_message_as_dict(role, message):

    return {"role": role, "content": message}

def message_dict_to_string(message):
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

    def __init__(self, systemP=params.nyako_prompt, summarizeP=params.summarize_prompt):
        self.systemP = format_message_as_dict("system", systemP)
        self.summarizeP = format_message_as_dict("system", summarizeP)
        self.messages = []
        self.memory = {}

    def query(self, message: str) -> str:
        self._add_message_to_history(message)
        response = self._get_response_from_model()

        if not response:
            return ""

        self._handle_response(response)
        return response

    def updateSystemPrompt(self, newPrompt):
        self.systemP = format_message_as_dict("system", newPrompt)

    def mostRecentMessage(self) -> dict:
        return self.messages[-1]

    def getContext(self) -> list:
        return self._build_context()

    def getLongTermMemory(self):
        return self._retrieve_long_term_memory()

    def memorize(self, messages):
        if messages is None or len(messages) == 0:
            return

        messages_string = "\n".join([message["content"] for message in messages])
        memory_management_input = [{"role": "user", "content": messages_string}]

        if self.memory != "":
            memory_management_input = [self.summarizeP] + [self.memory] + memory_management_input
        else:
            memory_management_input = [self.summarizeP] + memory_management_input

        memory_response = get_response(memory_management_input, params.summarization_model)

        if memory_response is None:
            return

        insertToMemory(memory_response, "\n".join([message_dict_to_string(message) for message in messages]))
        self.memory = format_message_as_dict("user", "[short-term memory] " + memory_response)

    def memorizeOldest(self, num_messages):
        self._memorize_oldest_messages(num_messages)

    def memorizeAll(self):
        self._memorize_all_messages()

    def _add_message_to_history(self, message):
        timeString = datetime.now().strftime("%m/%d/%Y, %H:%M:%S ")
        self.messages.append(format_message_as_dict("user", timeString + message))
        print(self.getContext())

    def _get_response_from_model(self):
        return get_response(self.getContext())

    def _handle_response(self, response):
        if(response.startswith("[listening]")):
            response = "[listening]"
        self.messages.append(format_message_as_dict("assistant", response))
        if(len(self.messages) > params.messages_count_before_summarization and params.memorize_enabled):
            self.memorizeOldest(params.num_messages_to_summarize)

    def _build_context(self):
        context = [self.systemP]
        ltm = self.getLongTermMemory()
        if ltm:
            context.append(ltm)
        if self.memory:
            context.append(self.memory)
        context += self.messages
        return context

    def _retrieve_long_term_memory(self):
        memoryChunks = retrieveMemoriesWithContext(self.mostRecentMessage()["content"], params.ltm_retrieval_count, params.ltm_context_size)
        if len(memoryChunks) == 0:
            return None
        return self._format_memory_chunks(memoryChunks)

    def _format_memory_chunks(self, memoryChunks):
        aggregateText = "[long-term memory]\n"
        count = 0
        for chunk in memoryChunks:
            astext = "\n".join([message.origin_messages for message in chunk])
            aggregateText += "MEMORY " + str(count) + ": " + astext + "\n"
            count += 1
        return format_message_as_dict("user", aggregateText)

    def _memorize_oldest_messages(self, num_messages):
        oldest_messages = self.messages[:num_messages]
        self.memorize(oldest_messages)
        self.messages = self.messages[num_messages:]

    def _memorize_all_messages(self):
        self.memorize(self.messages)
        self.messages = []