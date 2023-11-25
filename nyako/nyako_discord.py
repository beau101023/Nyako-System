import discord
import asyncio
from params import DISCORD_BOT_TOKEN
from params import nyako_prompt
from LLM.nyako_llm import ConversationSession

intents = discord.Intents.default()
intents.message_content = (
    True
)

bot = discord.Bot(intents=intents)
conversationChannel = None

messages = []

@bot.event
async def on_message(message: discord.Message):
    global conversationChannel
    global messages

    print(message.content)
    
    # Make sure we won't be replying to ourselves.
    if message.author.id == bot.user.id:
        return

    if(conversationChannel == None):
        conversationChannel = message.channel

    if(message.channel != conversationChannel):
        return

    messages.append(message)

# ready event
@bot.event
async def on_ready():
    print("Starting message collection...")
    loop = asyncio.get_event_loop()
    task = loop.create_task(collect_messages())


ConversationSession = ConversationSession(nyako_prompt)
emptyMessageCount = 0
# this method should run every 5 seconds or so to get chunks of messages
async def collect_messages():
    global messages
    global conversationChannel
    global emptyMessageCount

    while True:
        if(conversationChannel != None):
            try:
                if(emptyMessageCount == 12):
                    resp = ConversationSession.query("[no input (1:00)]")

                    if(resp != "" and resp != "[listening]"):
                        await conversationChannel.send(resp)
                    
                if(len(messages) == 0):
                    emptyMessageCount += 1
                    # wait 5 seconds for more messages to come in
                    await asyncio.sleep(5)
                else:
                    emptyMessageCount = 0

                    await asyncio.sleep(5)
                    # get whatever messages are in the buffer
                    messagesToProcess = messages

                    # clear the buffer
                    messages = []

                    # get the content of each message and format as [discord username]: [message content]
                    messagesToProcess = ["[discord] " + message.author.display_name + ": " + message.content for message in messagesToProcess]

                    # join the messages into a string separated by newlines
                    messagesToProcess = "\n".join(messagesToProcess)

                    resp = ConversationSession.query(messagesToProcess)

                    if(resp != ""):
                        await conversationChannel.send(resp)
            except Exception as e:
                try:
                    await conversationChannel.send("Error: " + str(e))
                    exit()
                except Exception as e:
                    print(e)
                    exit(1)
        else:
            await asyncio.sleep(5)

print("Starting bot...")
bot.run(DISCORD_BOT_TOKEN)