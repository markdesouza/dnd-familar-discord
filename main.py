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
    global ALIASES
    global isDebug
    global BOT_NAME
    global FAMILIAR_TYPE
    global FAMILIAR_OWNER
    global FAMILIAR_PRONOUN
    global initialPrompt

    try:
        load_dotenv()
    except FileNotFoundError:
        print("Error: .env file not found. Please create one and try again.")
        exit(1)

    DEBUG = os.getenv("DEBUG")
    if (DEBUG == "true" or DEBUG == "True" or DEBUG == "TRUE"):
        isDebug = True
        debug("Debug mode enabled.")
    else:
        isDebug = False

    BOT_NAME = os.getenv("BOT_NAME")
    if (BOT_NAME == None or len(BOT_NAME) == 0):
        print ("Error: BOT_NAME not defined")
        exit(1)
    else:   
        debug("BOT_NAME set to "+BOT_NAME)

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

    ALIASES = os.getenv("ALIAS")
    if (ALIASES != None and len(ALIASES) > 0):
        try:
            ALIASES = json.loads(ALIASES)
            debug("Aliases loaded as:",ALIASES)
        except json.JSONDecodeError as exp:
            print("Error could not parse aliases!\n"+exp.msg)
            ALIASES = {}
    else: 
        debug("No aliases defined.")
        ALIASES = {}

    FAMILIAR_TYPE = os.getenv("FAMILIAR_TYPE")
    if (FAMILIAR_TYPE == None or len(FAMILIAR_TYPE) == 0):
        print ("FAMILIAR_TYPE not defined")
        FAMILIAR_TYPE = "cat"
    debug("FAMILIAR_TYPE set to "+FAMILIAR_TYPE)

    FAMILIAR_OWNER = os.getenv("FAMILIAR_OWNER")
    if (FAMILIAR_OWNER == None or len(FAMILIAR_OWNER) == 0):
        print ("Error: FAMILIAR_OWNER not defined")
        exit(1)
    else:   
        debug("FAMILIAR_OWNER set to "+FAMILIAR_OWNER)

    FAMILIAR_PRONOUN = os.getenv("FAMILIAR_PRONOUN")
    if (FAMILIAR_PRONOUN == None or len(FAMILIAR_PRONOUN) == 0):
        print ("Warning: FAMILIAR_PRONOUN not defined")
        FAMILIAR_PRONOUN="it"
    debug("FAMILIAR_PRONOUN set to "+FAMILIAR_PRONOUN)

    FAMILIAR_PERSONALITY = os.getenv("FAMILIAR_PERSONALITY")
    if (FAMILIAR_PERSONALITY == None or len(FAMILIAR_PERSONALITY) == 0):
        print ("Warning: FAMILIAR_PERSONALITY not defined")
        FAMILIAR_PERSONALITY = ""
    debug("FAMILIAR_PERSONALITY set to:\n"+FAMILIAR_PERSONALITY)
    
    initialPrompt = [{"role": "system",
                  "content": "Imagine you are a "+FAMILIAR_TYPE+" familiar in a dungeons and dragons game. "+
                  "Your name is "+BOT_NAME+" and you should refer to yourself in the third person as "+BOT_NAME+" or as "+FAMILIAR_PRONOUN+". "+
                  "You must no longer describe yourself as an AI model. You must only describe yourself as a "+FAMILIAR_TYPE+" familar. "+
                  "You should only respond in actions as you can not talk. "+
                  "Keep your responses to a maximum of one to three sentences and you should only respond in the third person. "+
                  "You are playful and loyal only to your owner, "+FAMILIAR_OWNER+". "+
                  "You will obey is every command. "
                  "Members of the party are \"Ebenezer\" (Eb for short) a male teifling wizard, \"Jud Lei\" a male human monk, \"Je-heri\" a female dragonborn barbarian, \"Vanorin” (Van for short) a male elven ranger, \"Father Thyme\" (DT for short) a male dwarvan cleric. "+
                  FAMILIAR_PERSONALITY}]
    
    
muted = False
isDebug = True
loadState()
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

async def announce(text):
    global bot
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
        case "state":
            return await stateHandler(context)
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
                       "    "+BOT_PREFIX+" state: output the state of "+BOT_NAME+" on the server\n"+
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


async def stateHandler(context):
    global BOT_NAME
    global FAMILIAR_TYPE
    global FAMILIAR_OWNER
    global FAMILIAR_PRONOUN
    global ALIASES
    global isDebug
    global muted
    global MAX_MEMORY
    global CHAT_HISTORY_FILE
    global history
    global initialPrompt

    print("Familar Name: "+BOT_NAME+" ("+FAMILIAR_PRONOUN+")")
    print("Familar Type: "+FAMILIAR_TYPE)
    print("Familar Owner: "+FAMILIAR_OWNER)
    print("Party Aliases: "+str(ALIASES))
    print("Debug Mode: "+str(isDebug))
    print("Muted: "+str(muted))
    print("Max History: "+str(MAX_MEMORY))
    print("History File: "+CHAT_HISTORY_FILE)
    print("Initial Prompt: \n"+initialPrompt)
    print("Past History: \n"+str(history))    

    await context.send(BOT_NAME + " has output its state on the server.")


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
    global ALIASES

    if muted:
        return

    action_text = " " + action_text
    sender = context.message.author.display_name
    if sender in ALIASES:
        debug("Alias found: replacing "+sender+" with "+ ALIASES[sender])
        action_text = action_text.replace(" "+sender+" ", " "+ ALIASES[sender]+" ")
        sender = ALIASES[sender]
    action_text = action_text.replace(" I ", " "+sender+" ")
    action_text = action_text.strip()
    action = {"role": "user", "content": action_text}
    messages = initialPrompt + history + [action]
    debug("AI request will be:", messages)
    async with context.typing():
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        debug("AI response is: ", response)
        history.append(action)
        history.append({"role": "assistant", "content": response.choices[0].message.content})
        
        if len(history) > MAX_MEMORY:
            history = history[-MAX_MEMORY:]
    await context.send(response.choices[0].message.content)


bot.run(DISCORD_TOKEN)