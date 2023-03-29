import openai
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json

load_dotenv()
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

CHAT_HISTORY_FILE = os.getenv("CHAT_HISTORY_FILE")
print(CHAT_HISTORY_FILE)
if (CHAT_HISTORY_FILE == None or len(CHAT_HISTORY_FILE) == 0):
    print ("Using chat_history.json as the default chat history filename.")
    CHAT_HISTORY_FILE = "chat_history.json"

history = []
muted = False


async def announce(text):
    for channel in bot.get_all_channels():
        if channel.type.name == 'text':
            await bot.get_channel(channel.id).send(text)


@bot.event
async def on_ready():
    await announce(BOT_NAME + " enters the chat!")


@bot.command(name=BOT_CMD, help="Talk to "+BOT_NAME)
async def baseCmd(context, action_text):
    action_text = context.message.content[len(BOT_PREFIX)+1:]
    match action_text:
        case "help":
            return await reset(context)
        case "reset":
            return await reset(context)
        case "save":
            return await save(context)
        case "mute":
            return await mute(context)
        case "unmute":
            return await unmute(context)
        case _:
            return await interact(context, action_text)


async def help(context):
    # TODO
    await context.send("Not implemented yet. Sorry :(")


async def reset(context):
    global history
    load_dotenv()
    history = []
    if os.path.isfile(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as infile:
            try:
                history = json.load(infile)
            except json.JSONDecodeError as exp:
                print(exp.msg)
    print(history)
    await context.send(BOT_NAME + " essence revived from her latest bottle.")


async def save(context):
    global history
    with open(CHAT_HISTORY_FILE, "w") as outfile:
        json.dump(history, outfile)
    await context.send(BOT_NAME + " essence has been distilled and bottled.")


async def mute(context):
    global muted
    muted = True
    await context.send(BOT_NAME + " will now remain quiet :(")


async def unmute(context):
    global muted
    muted = False
    await context.send(BOT_NAME + " is now free to speak. :)")


async def interact(context, action_text):
    global muted
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
    await context.send(response.choices[0].message.content)

bot.run(DISCORD_TOKEN)
