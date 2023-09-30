import openai


from nyako_params import API_KEY
from nyako_params import summarize_prompt
from nyako_params import messages_count_before_summarization
from nyako_params import num_messages_to_summarize
from nyako_params import chat_model
from nyako_params import summarization_model

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

    def __init__(self, systemP, summarizeP=summarize_prompt):

        self.systemP = format_message_as_dict("system", systemP)

        self.summarizeP = format_message_as_dict("system", summarizeP)

        self.messages = []

        self.memory = ""
    

    def query(self, message):

        self.messages.append(format_message_as_dict("user", message))

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

            return [self.systemP] + self.messages

        return [self.systemP] + [self.memory] + self.messages


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

        # Input is the oldest messages, the previous memory, and the summarization prompt

        messages_string = "\n".join([message_dict_to_string(message) for message in oldest_messages])

        if(self.memory == ""):
            memory_management_input = [{"role": "user", "content": messages_string}]
        else:
            memory_management_input = [{"role": "user", "content": message_dict_to_string(self.memory) + "\n" + messages_string}]
        
        memory_management_input = [self.summarizeP] + memory_management_input

        print("memory_management_input: ")
        print(memory_management_input)

        memory_response = get_response(memory_management_input, summarization_model)
        print("memory response: ")
        print(memory_response)

        # tag the summary so the llm will interpret it as memory
        self.memory = format_message_as_dict("user", "[short-term memory] " + memory_response)
        print("formatted memory: ")
        print(self.memory)