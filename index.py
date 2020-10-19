import discord
from discord.ext import commands
import pymongo, os
from dotenv import load_dotenv

load_dotenv()



extensions=['moderation','utility','fun']



def get_prefix(bot,msg):
    bot_prefixes=['.']

    return commands.when_mentioned_or(*bot_prefixes)(bot,msg)





bot= commands.Bot(command_prefix=get_prefix,description="Your bot description here")






@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")


def loadExtensions():
    loadFail=[]
    for ext in extensions:
        try:
            bot.load_extension(ext)
            print("Loaded",ext)
        except Exception:
            loadFail.append(ext)

    if loadFail:
        print(f"\n\n\n----------------\nFailed to load: {', '.join(loadFail)}")
        return loadFail



def runBot():
    loadExtensions()
    token=os.getenv('TOKEN')
    if token is not None:
        print("Running bot now...")
        bot.run(token)

    print("Environment Variable TOKEN not found")
    raise KeyError


runBot()