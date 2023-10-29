import openai

from datetime import datetime

from params import API_KEY
from params import summarize_prompt
from params import nyako_prompt
from params import messages_count_before_summarization
from params import num_messages_to_summarize
from params import chat_model
from params import summarization_model
from params import memorize_enabled

from vectordb.nyako_ltm import insertToMemory
from vectordb.nyako_ltm import retrieveMemoriesWithContext
from params import ltm_context_size
from params import ltm_retrieval_count

openai.api_key = API_KEY


def get_response(messages, model=chat_model):

    response = openai.ChatCompletion.create(

        model = model,

        messages = messages

    )

    return response.choices[0].message["content"]


def format_message_as_dict(role, message):

    return {"role": role, "content": message}

def message_dict_to_string(message):
        return message["role"] + ": " + message["content"]


# an object that stores a history of messages and a system prompt

class ConversationSession:

    def __init__(self, systemP=nyako_prompt, summarizeP=summarize_prompt):

        self.systemP = format_message_as_dict("system", systemP)

        self.summarizeP = format_message_as_dict("system", summarizeP)

        self.messages = []

        self.memory = ""
    

    def query(self, message):

        timeString = datetime.now().strftime("%m/%d/%Y, %H:%M:%S ")
        self.messages.append(format_message_as_dict("user", timeString + message))

        print(self.getContext())

        response = get_response(self.getContext())

        # if response starts with the data tag "[listening]" then remove everything after the tag
        if(response.startswith("[listening]")):
            response = "[listening]"

        self.messages.append(format_message_as_dict("assistant", response))

        # if the message context goes over [messages_count_before_summarization] messages, memorize the oldest messages
        if(len(self.messages) > messages_count_before_summarization):
            self.LLMMemorize()

        return response

    def mostRecentMessage(self):
        return self.messages[-1]


    # retrieves what'll be fed into the llm on the next query
    def getContext(self):

        if(self.memory == ""):
            return [self.systemP] + [self.getLongTermMemory()] + self.messages
        else:
            return [self.systemP] + [self.getLongTermMemory()] + [self.memory] + self.messages

    def getLongTermMemory(self):
        memoryChunks = retrieveMemoriesWithContext(self.mostRecentMessage()["content"], ltm_retrieval_count, ltm_context_size)
        
        aggregateText = "[long-term memory]\n"
        count = 0
        for chunk in memoryChunks:
            astext = "\n".join([message.origin_messages for message in chunk])
            aggregateText += "MEMORY " + str(count) + ": " + astext + "\n"
            count += 1

        return format_message_as_dict("user", aggregateText)

    # prints the conversation history
    def printFormattedMessageLog(self):
            for message in self.messages:
                print(message["role"] + ": " + message["content"])


    # queries the llm to summarize the conversation up to this point, then discards the conversation in favor of the summary
    def LLMMemorize(self):

        # get the oldest [messages_to_summarize] messages

        oldest_messages = self.messages[:num_messages_to_summarize]
        print("oldest_messages: ")
        print(oldest_messages)

        # remove the oldest messages from the conversation
        self.messages = self.messages[num_messages_to_summarize:]

        if(not memorize_enabled):
            return

        # Input is the oldest messages, the previous memory, and the summarization prompt
        messages_string = "\n".join([message["content"] for message in oldest_messages])
        memory_management_input = [{"role": "user", "content": messages_string}]
        if(self.memory != ""):
            memory_management_input = [self.summarizeP] + [self.memory] + memory_management_input
        else:
            memory_management_input = [self.summarizeP] + memory_management_input

        print("memory_management_input: ")
        print(memory_management_input)

        memory_response = get_response(memory_management_input, summarization_model)

        print("memory response: ")
        print(memory_response)

        # insert the summary and the original messages into the long term memory
        insertToMemory(memory_response, "\n".join([message_dict_to_string(message) for message in oldest_messages]))

        # tag the summary so the llm will interpret it as memory
        self.memory = format_message_as_dict("user", "[short-term memory] " + memory_response)
        print("formatted memory: ")
        print(self.memory)