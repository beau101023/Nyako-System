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

        self.messages.append(format_message_as_dict("assistant", response))


        # if the message context goes over [messages_count_before_summarization] messages, memorize the oldest messages

        if(len(self.messages) > messages_count_before_summarization):

            self.LLMMemorize()

        return response


    def fakeQuery(self, message):

        self.messages.append(format_message_as_dict("user", message))

        response = ""

        self.messages.append(format_message_as_dict("assistant", response))


        # if the message context goes over [messages_count_before_summarization] messages, memorize the oldest messages

        if(len(self.messages) > messages_count_before_summarization):

            self.LLMMemorize()

        return response



    def mostRecentMessage(self):

        return self.messages[-1]


    # retrieves what's fed into the llm

    def getContext(self):

        if(self.memory == ""):

            return [self.systemP] + self.messages

        return [self.systemP] + [self.memory] + self.messages


    # queries the llm to summarize the conversation up to this point, then discards the conversation in favor of the summary

    def LLMMemorize(self):

        # get the oldest [messages_to_summarize] messages

        oldest_messages = self.messages[:num_messages_to_summarize]
        print("oldest_messages: ")
        print(oldest_messages)

        # remove the oldest messages from the conversation
        self.messages = self.messages[num_messages_to_summarize:]

        # use GPT-4 for summarization due to higher accuracy. Input is the oldest messages, the previous memory, and the summarization prompt

        if(self.memory == ""):
            memory_management_input = [self.summarizeP] + oldest_messages
        else:
            memory_management_input = [self.summarizeP] + [self.memory] + oldest_messages
        print("memory_management_input: ")
        print(memory_management_input)

        memory_response = get_response(memory_management_input, summarization_model)
        print("memory response: ")
        print(memory_response)

        # tag the summary so the llm will interpret it as memory

        self.memory = format_message_as_dict("assistant", "[short-term memory]: " + memory_response)
        print("formatted memory: ")
        print(self.memory)