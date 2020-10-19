import discord, asyncio
from discord.ext import commands
from discord.ext.commands import command
import random, time
import typing


class Fun(commands.Cog):
    def __init__(self,bot):
        """
        {
            "userId": {
                "daily": time.time():float,  --- > to reach 24 hours
                "cash": cashValue:int

            }
        }
        """
        self.bot=bot
        self.localData={}



    async def createUserData(self,userId):
        self.localData[userId] = {
            'daily' : time.time() -3,
            'cash': 0
        }


    @command(name='8ball')
    async def eball(self,msg,*,message):
        return await msg.send("No")


    @command(aliases=['av'])
    async def avatar(self,msg,user:discord.Member=None):
        if user is None:
            user = msg.author
        
        return await msg.send(user.avatar_url)

    @commands.has_permissions(administrator=True)
    @command()
    async def say(self,msg,channel:typing.Optional[discord.TextChannel]=None, *,message):
        if channel is None:
            channel = msg.channel
        return await channel.send(message)

    @command(aliases=['invcr'])
    async def invitecreate(self,msg):
        code = await msg.channel.create_invite()
        return await msg.send(code)



    @command()
    async def coin(self,msg,bet:int,value:str):
        if msg.author.id not in self.localData:
            await self.createUserData(msg.author.id)
        result= random.choice(['heads','tails'])
        if value == result:
            return await msg.send(f"Congrats you got {bet}, it was {result}")
            self.localData[msg.author.id]['cash'] +=bet

        self.localData[msg.author.id]['cash'] -= bet
        return await msg.send(f"You've lost {bet}, it was {result}")



    @command(aliases=['$'])
    async def cash(self,msg,user:discord.Member = None):
        if user is None:
            user = msg.author
        
        if user.id in self.localData:
            return await msg.send(self.localData[user.id]['cash'])
        
        return await msg.send(f"{user.name} is broke or not in database yet")



    @commands.has_permissions(administrator=True)
    @command(aliases=['award'])
    async def grant(self,msg,amt:int,user:discord.Member):
        if user.id not in self.localData:
            await self.createUserData(user.id)

        self.localData[user.id]['cash'] += amt
        return await msg.send(f"Added {amt} to {user.name}")


    @command()
    async def give(self,msg,value:int,user:discord.Member):
        if msg.author.id in self.localData and self.localData[msg.author.id]['cash'] >= value:
            if user.id not in self.localData:
                await self.createUserData(user.id)

            
            self.localData[user.id]['cash'] += value
            self.localData[msg.author.id] -= value
            return await msg.send(f"{value} gifted to {user.name}")

        return await msg.send("You do not have enough cash")



    @command()
    async def daily(self,msg):
        dailyValue =  192819 #NOTE Enter your amout here
        
        if msg.author.id in self.localData:
            timer=self.localData[msg.author.id]['daily']
            if time.time() >= timer:
                self.localData[msg.author.id]['cash'] += dailyValue
                self.localData[msg.author.id]['daily'] = time.time() + 86400
                return await msg.send("Daily rewards claimed")

            return await msg.send(f"There is still {round(timer/120,3)} more hours before you can use the command again")

        await self.createUserData(msg.author.id)
        self.localData[msg.author.id]['daily'] += time.time()+ 86400
        self.localData[msg.author.id]['cash'] +=dailyValue
        return await msg.send("Daily reward claimed")


def setup(bot):
    bot.add_cog(Fun(bot))
