import discord, asyncio
from discord.ext import commands
from discord.ext.commands import command
import random, time
import typing


class Utility(commands.Cog):
    def __init__(self,bot):
        self.bot = bot


    @command()
    async def checkCommand(self,msg):
        return await msg.send("Check success!")




def setup(bot):
    bot.add_cog(Utility(bot))