import openai
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json

def debug(*args):
    global isDebug
    if (isDebug):
        for item in args:
            print("DEBUG: ", end="")
            print(item)

def loadState():
    global MAX_MEMORY
    global CHAT_HISTORY_FILE
    global history

    try:
        load_dotenv()
    except FileNotFoundError:
        print("Error: .env file not found. Please create one and try again.")
        exit(1)

    try:
        MAX_MEMORY_STR = os.getenv("MAX_MEMORY")
        MAX_MEMORY = int(MAX_MEMORY_STR)
        debug("MAX_MEMORY set to "+str(MAX_MEMORY))
    except ValueError:
        print("Warning: MAX_MEMORY defaulted to 10 interactions. Check your .env file")
        MAX_MEMORY=10
    
    history = []
    CHAT_HISTORY_FILE = os.getenv("CHAT_HISTORY_FILE")
    if (CHAT_HISTORY_FILE == None or len(CHAT_HISTORY_FILE) == 0):
        print ("Using chat_history.json as the default chat history filename.")
        CHAT_HISTORY_FILE = "chat_history.json"
    else:
        debug("CHAT_HISTORY_FILE set to "+CHAT_HISTORY_FILE)
    if os.path.isfile(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as infile:
            try:
                history = json.load(infile)
                debug("Chat History loaded as:",history)
                infile.close()
            except json.JSONDecodeError as exp:
                print("Error could not parse chat history!\n"+exp.msg)

muted = False
isDebug = False
loadState()
BOT_NAME = os.getenv("BOT_NAME")
BOT_PREFIX = "/"+BOT_NAME.lower()
if (len(BOT_PREFIX) < 2):
    print("Error: BOT_PREFIX must be at least 2 characters long")
    exit(1)
BOT_CMD_PREFIX = BOT_PREFIX[:-1]
BOT_CMD = BOT_PREFIX[-1]

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if (len(DISCORD_TOKEN) != 72):
    print("Error: DISCORD_TOKEN does not appear to be set correctly in your .env file. Should be 72 characters long.")
    exit(1)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_CMD_PREFIX, intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")
if (len(openai.api_key) != 51):
    print("Error: OPENAI_API_KEY does not appear to be set correctly in your .env file. Should be 51 characters long.")
    exit(1)
initialPrompt = [{"role": "system",
                  "content": "Imagine you are a cat familiar in a dungeons and dragons game. Your name is Tinder and you should refer to yourself in the third person as Tinder or she. You should only respond in actions as you can not talk. Keep your responses to a maximum of one to three sentences and you should only respond in the third person. You are playful and loyal only to your owner,  Ebenezer. You will obey is every command. You will interact with other members of the party but your untrusting nature means that you have a short fuse if attacked or negatively interacted with. Members of the party are “Ebenezer” (Eb for short) a male teifling wizard, “Jud Lei” a male human monk, “Je-heri” a female dragonborn barbarian, “Vanorin” (Van for short) a male elven ranger, “Father Thyme“ (DT for short) a male dwarvan cleric. If pushed you can cast the following magic spells, Create Bonfire, Fire Bolt, Mage Hand, Thaumaturgy. You should use Thaumaturgy to intimidate an aggressor by either glowing eyes or hissing loudly. You should cast Mage Hand to grab objects that you want to grab or eat. Cast Fire Bolt to attack things far away. Cast create bonfire, to  destroy an object. You may do damage to party members if repeatedly attacked by them. You can also use your claws to defend yourself. If there is an attack or damage roll for a dice, you should state in a 4th sentence: “Attack: (dice type) Damage: (dice type)”. You really like to play will wool and string and can become distracted with focused lights. When shown milk, cheese, a rat or a mouse, you will instinctively attempt to eat it."}]

async def announce(text):
    for channel in bot.get_all_channels():
        if channel.type.name == 'text':
            await bot.get_channel(channel.id).send(text)


@bot.event
async def on_ready():
    await announce(BOT_NAME + " has entered the chat! (type '"+BOT_PREFIX+" help' for more info)")


@bot.command(name=BOT_CMD, help="Talk to "+BOT_NAME)
async def baseCmd(context, action_text):
    action_text = context.message.content[len(BOT_PREFIX)+1:]
    debug("Received request: "+action_text)
    match action_text:
        case "help":
            return await helpHandler(context)
        case "reset":
            return await resetHandler(context)
        case "save":
            return await saveHandler(context)
        case "mute":
            return await muteHandler(context)
        case "unmute":
            return await unmuteHandler(context)
        case "debug":
            return await debugHandler(context)
        case _:
            return await interactionHandler(context, action_text)


async def helpHandler(context):
    await context.send("Commands:\n"+
                       "    "+BOT_PREFIX+" help: show this message\n"+
                       "    "+BOT_PREFIX+" save: save all interactions currently made with "+BOT_NAME+". Useful when ending a session.\n"+
                       "    "+BOT_PREFIX+" reset: reset "+BOT_NAME+" to last saved state. Useful when starting a session or to undo negative interactions.\n"+
                       "    "+BOT_PREFIX+" mute: prevent "+BOT_NAME+" from responding to interactions\n"+
                       "    "+BOT_PREFIX+" unmute: allow "+BOT_NAME+" to responding to interactions\n"+
                       "    "+BOT_PREFIX+" debug: toggle display debugging information on the server\n"+
                       "    "+BOT_PREFIX+" <interaction>: interact with "+BOT_NAME+"\n"+
                       "\n"+
                       "Interaction examples:\n"+
                       "    "+BOT_PREFIX+" I pet "+BOT_NAME+"\n"+
                       "    "+BOT_PREFIX+" I give "+BOT_NAME+" some cheese\n");


async def resetHandler(context):
    loadState()
    await context.send(BOT_NAME + " essence revived from her latest bottle.")


async def saveHandler(context):
    global history
    with open(CHAT_HISTORY_FILE, "w") as outfile:
        json.dump(history, outfile)
    await context.send(BOT_NAME + " essence has been distilled and bottled.")


async def muteHandler(context):
    global muted
    muted = True
    await context.send(BOT_NAME + " will now remain quiet :(")


async def unmuteHandler(context):
    global muted
    muted = False
    await context.send(BOT_NAME + " is now free to speak. :)")

async def debugHandler(context):
    global isDebug
    if isDebug:
        debug("Debugging now disabled")
        isDebug = False
        await context.send(BOT_NAME + " will no longer output debugging information on the server.")
    else:
        isDebug = True
        debug("Debugging now enabled")
        await context.send(BOT_NAME + " will now output debugging information on the server.")

async def interactionHandler(context, action_text):
    global muted
    global history

    if muted:
        return

    sender = context.message.author.display_name
    action_text = " " + action_text
    action_text = action_text.replace(" I ", " "+sender+" ")
    action_text = action_text.strip()
    action = {"role": "user", "content": action_text}
    messages = initialPrompt + history + [action]
    print(messages)
    print()
    async with context.typing():
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        print(response)
        history.append(action)
        history.append(
            {"role": "assistant", "content": response.choices[0].message.content})
        
        if len(history) > MAX_MEMORY:
            history = history[-MAX_MEMORY:]
    await context.send(response.choices[0].message.content)

bot.run(DISCORD_TOKEN)