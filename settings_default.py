import torch

from openai import AsyncOpenAI

## big flags

# extra printing stuff
debug_mode = False

# RAG memory
memorize_enabled = False

# audio input parameters
FramesPerBuffer = 512 # every buffer is 32ms of audio (at 16kHz)
INPUT_SAMPLING_RATE = 16000
speech_sensitivity_threshold = 0.6

# Silero text to speech parameters
sample_rate_out = 24000
language = 'en'
model_id = 'v3_en'
speaker = 'en_56'

# lowest explored speaker: en_1
# highest explored speaker: en_91

# en_56 : fairly high pitched, most promising
# en_11 : pretty good, sorta noisy?

# en_24 : standard woman
# en_51 : more whispery
# en_21 : very british
# en_53 : aussie
# en_59 : older woman sounding
# en_74 : valley girl?
# en_80 : robotic

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Running on ' + device.type + '.')

# tokens, keys
DISCORD_BOT_TOKEN = open("discord_bot_token.txt", "r").read().strip()
OPENAI_API_KEY = open("openai_api_key.txt", "r").read().strip()

# openai access object and params
ASYNCOPENAI = AsyncOpenAI(api_key=OPENAI_API_KEY)
summarization_model = "gpt-4o-mini"
chat_model = "gpt-4o-mini"

chat_model_prompt = """You are Nyako, a catgirl. :3"""

# llm short term memory params
max_context_len = 20
num_messages_to_summarize = 4
# short term memory prompts
long_memory_prompt = "You are MemoryGPT. Summarize the conversation between Nyako and the users. Discard unimportant facts. Include important facts from the previous short term memory if there is one.\n\nIN:\n\"Beau: Nyako stay in this channel ok\nNyako: Alright, I'll stick around in this channel, Beau101023! :3 * takes a cozy nap in the corner *\nWolvered: Nyako can you write the longest message you can muster?\nNyako: Nyya~! :3 I'll try to make it as nyice as pawsible for you, Wolvered!\nWolvered: Nyako, write the longest message possible\"\nOUT:\n- Beau asks Nyako to stay in the channel.\n- Nyako agrees to stay and takes a nap.\n- Wolvered asks Nyako to write the longest message possible.\n- Nyako agrees and is excited to do so.\n\nIN: \"lonama184: today I went to a flower shop, then the park, but that night I felt real sick and I had to go to the doctor. Turns out I had appendicitis!!\"\n- lonama184 told nyako about their day, which included a hospital visit for appendicitis\n\nIN: \"Nyako: Mmm? What dyoes \"Mmm\" mean? Don't keep the paranormal secrets from me, Meow~hic* (^ w ^)<\nBeau: now it's collecting all the data from her convos so I can have lots of example stuff :)\nNyako: By catty feline standards, that sounds a bit weird, but as lonag as it helps with cations, maybe that's Pallright. :3\nBeau: I can be just like all the horrible companies :)\"\nOUT:\n- Nyako asks about the meaning of \"Mmm\" and is curious about paranormal secrets.\n- Beau mentions collecting data for examples.\n- Nyako comments on it being weird but okay.\n- Beau jokes about being like horrible companies."
short_memory_prompt = "You are MemoryGPT. Summarize the conversation between Nyako and the users. Discard unimportant facts. Include important facts from the previous short term memory if there is one."

# Use the long memory prompt with the cheaper LLMs and the short memory prompt with the more capable ones.
summarize_prompt = long_memory_prompt

# long term memory params
ltm_context_size = 0
ltm_retrieval_count = 2
similarity_threshold = 0.4 # 0.0 is disabled

# input chunker params
default_no_input_interval_seconds = 60
default_processor_delay = 1