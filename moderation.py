import discord, asyncio
from discord.ext import commands
from discord.ext.commands import command
import random, time
import typing, random
import pymongo



class Administration(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.database=None
        self.connect_database()

    def connect_database(self):
        """
        A connetion to the database to mongodb will be attempted if the connectionURL variable is not None
        """
        connectionURL="mongodb.//localhost:27017" #NOTE shold be later renamed to your client connection to mongodb
        try:
            connection=pymongo.MongoClient(connectionURL,connect=True)
            collection = connection['database']['discordBot']
            if collection.find_one({'_id':'botDatabase'}) is None:
                document = {'_id':'discordBOt'}
                self.database = collection.insert_one(document)
                setattr(self,'connected',True)
                setattr(self,'localData',document)
            
        except:
            print("Failed to connect to database, setting a local dict")
            setattr(self,'localData',{})




    def evalString(self,string,object):
        start=string.find('{')
        end=string.find('}')
        makeEval=eval(string[start+1:end])
        string=string.replace(f'{string[start:end+1]}',makeEval)
        return string

    async def checkEvalString(self,string):
        acceptedVars=['user.name','user.id','server.name','server.id']
        start=string.find('{')
        end=string.find('}')
        placeHolder=string[start+1:end]
        if placeHolder in acceptedVars:
            return True, True

        return False, acceptedVars


    async def dataCheck(self,msg):

        if str(msg.guild.id) in self.localData:
            return True

        self.localData[str(msg.guild.id)]= {
            'mutedUsers': {},
            'muteRole':None,
            'warnings':{}, #{userId:warningAmt}
            'greetings':{
                "channel":None,
                "messages":['welcome to the server {user.name} {server.name}'] # default greetings message will be included
            }
        }


        return False


    async def muteFromChannels(self,msg,_target):
        channels=await msg.guild.text_channels
        newPerms= discord.PermissionOverwrite(read_messages=False,send_messages=False,add_reactions=False)
        failed_channels=[]
        for channel in channels:
            try:
                await channel.set_permissions(target=_target,overwrite=newPerms)
            except:
                failed_channels.append(channel.name)
            
        if failed_channels:
            return await msg.send(f"Could not mute {_target.name} in {' '.join(failed_channels)}.")

        return await msg.send(f"User {_target} muted")

    async def eventTrackerLoop(self):
        while True:
            for guild in self.localData.copy():
                for users,timer in self.localData[guild]['mutedUsers'].items():
                    if timer <= time.time():
                        self.localData[guild]['mutedUsers'].pop(users)

            await asyncio.sleep(1)

    @commands.Cog.listener(name='on_member_join')
    async def user_joins_guild(self,member):
        """
        The function will run once a member joins the guild that the bot is in.
        Variable name must be inside curly brackets {user.name} -- > Cheng Yue
        """
        if str(member.guild.id) in self.localData:
            chan=member.guild.get_channel(self.localData[str(member.guild.id)]['greetings']['channel'])
            if chan is not None:
                rawMessage = random.choice(self.localData[str(member.guild.id)]['greetings']['message'])
                if 'user.' in rawMessage:
                    message = self.evalString(rawMessage,member)

                if 'server.' in rawMessage:
                    message = self.evalString(rawMessage,member.guild)

                return await chan.send(message)



    @commands.has_permissions(manage_channels=True)
    @command(name='creatextchnl',aliases=['ctch'])
    async def createTextChannel(self,msg,*,channelName):
        chan=await msg.guild.create_text_channel(name=channelName)
        return await msg.send(f"Created new text channel {chan.mention}")


    @commands.has_permissions(manage_channels=True)
    @command(name='deltxtchnl',aliases=['dtch'])
    async def deleteTextChannel(self,msg,channelName:discord.TextChannel):
        """
        Channel must be mentioned if name has spaces
        """
        try:
            await channelName.delete()
            return await msg.send(":white_check_mark:")
        except Exception:
            return await msg.send(f"Could not delete channel, {channelName}")



    @commands.has_permissions(manage_channels=True)
    @command(name='setchanlname',aliases=['schn'])
    async def setChannelName(self,msg,*,newName:str):
        await msg.channel.edit(name=newName)
        return await msg.send("Channel name changed")

    


    @commands.has_permissions(manage_channels=True)
    @command(name='settopic',aliases=['st'])
    async def setTopic(self,msg,*,newTopic:str):
        await msg.channel.edit(topic=newTopic)



    @commands.has_permissions(manage_roles=True)
    @command(name='setmuterole')
    async def setMuteRole(self,msg,muteRole:discord.Role):
        await self.dataCheck(msg)

        if self.localData[str(msg.guild.id)]['muteRole'] is None and muteRole.id == self.localData[str(msg.guild.id)]['muteRole']:
            return await msg.send("The role is already in database")




        self.localData[str(msg.guild.id)]['muteRole'] = muteRole.id
        channels=msg.guild.channels
        failed_channels=[]
        newPerms=discord.PermissionOverwrite(read_messages=False,send_messages=False)

        for chan in channels:
            try:
                await chan.set_permissions(target=muteRole,overwrite=newPerms)
            except:
                failed_channels.append(chan.name)

        if failed_channels:
            return await msg.send(f"Could not set mute role for {' '.join(failed_channels)}\nPlease check the permissions of the bot")

        return await msg.send("Mute roles set :white_check_mark:")




    @commands.has_permissions()
    @command()
    async def mute(self,msg,user:discord.Member,time:int=False):
        """
        user:
            discord member mentioned
        time:
            the amount of time user is muted in minutes
            if default mute is not provided, user will be mute until un-muted

        """
        #TODO: check if previous mute role exist to replace with new role
        self.localData['mutedUsers']={str(user.id):time}
        if await self.dataCheck(msg) is False:
            return await msg.send("Mute role setup is required.")
        if user.id in self.localData[str(msg.guild.id)]:
            return await msg.send("User is already muted")

        role=msg.guild.get_role(self.localData[str(msg.guild.id)])
        if time is False:
            #NOTE: Testing output
            await user.edit(roles=user.roles+role) 
        
        self.localData[str(msg.guild.id)]['mutedUsers'] ={user.id:time.time()+time*60}
        await user.edit(roles=user.roles+role)
        return await msg.send(f"USer {user.name} has been muted.")


        
    @commands.has_permissions(manage_roles=True)
    @command(name='unmute')
    async def unMute(self,msg,user:discord.Member):
        await self.dataCheck(msg)
        if user.id not in self.localData[str(msg.guild.id)]['mutedUsers']:
            return await msg.send("User is not muted")

        self.localData[str(msg.guild.id)]['mutedUsers'].pop(user.id)
        role=msg.guild.get_role(self.localData[str(msg.guild.id)]['muteRole'])
        if role is None:
            return await msg.send("Could not find the mute role, please remove the mute role manually from the user")
        
        newRoles=user.roles.copy()
        newRoles.pop(newRoles.index(role))
        await user.edit(roles=newRoles)
        return await msg.send("User has been un-muted.")
        


            #-----------------------------------------------------------------------------------------------

    @commands.has_permissions(manage_messages=True) #NOTE Need manage message 
    @command()
    async def prune(self,msg,limit:typing.Optional[int] = 100,user:discord.Member= None):
        """
        Deletes the message of bot if no arguments are provided or if `user` is missing
        """
        def isUser(msg):
            if user is None:
                return self.bot.user.id == msg.author.id

            return user.id == msg.author.id

        await msg.channel.purge(limit=limit,check=isUser)



    @commands.has_permissions(manage_roles=True)
    @command(name='createrole',aliases=['cr'])
    async def createRole(self,msg,*,roleName):
        role=await msg.guild.create_role(name=roleName,reason=f'Role created by {msg.author.name}')
        await msg.send(f"Created  new role {role.mention}")



    @commands.has_permissions(manage_roles=True)
    @command(name='deleterole',aliases=['dr'])
    async def deleteRole(self,msg,*,role:discord.Role):
        await role.delete(reason=f'Role {role.name} deleted by {msg.author.name}')
        return await msg.send(f"Role {role.name} has been deleted")



    @commands.has_permissions(manage_roles=True)
    @command(name='setrole',aliases=['sr'])
    async def setRole(self,msg,opts:commands.Greedy[typing.Union[discord.Role,discord.Member]]):
        """
        Add mentioned role(s) to the mentioned user(s)
        `Ex:` .addrole @User1 @User2 @Role1 @Role2
        `Ex:` .addrole @Role1 @Role2 @User1 @User2
        `Note:` roles --> users or users---> roles works 
        If no member mentioned then adds it to command user
        """
        roles=[role for role in opts if isinstance(role,discord.Role)]
        if not roles:
            return await msg.send(f"The mentioned role(s) or member(s) were not found\n{opts}")
        found_member=False
        for member in opts:
            if isinstance(member,discord.Member):
                #NOTE: member mentioned
                found_member=True
                await member.edit(roles=member.roles+roles)

        if found_member == False:
            #No members mentioned
            await msg.author.edit(roles=msg.author.roles+roles)
        return await msg.message.add_reaction(emoji='✅')



    @commands.has_permissions(manage_roles=True)
    @command(name='removerole',aliases=['rr'])
    async def removeRole(self,msg,opts:commands.Greedy[typing.Union[discord.Role,discord.Member]]):
        """
        Remove mentioned role(s) to the mentioned user(s)
        `Ex:` .removerole @User1 @User2 @Role1 @Role2
        `Ex:` .removerole @Role1 @Role2 @User1 @User2
        `Note:` Order doesn't matter as long as user and role is mentioned
        """

        remove_roles=[role.id for role in opts if isinstance(role,discord.Role)]
        found_member=False
        new_roles=[]
        if not remove_roles:
            return await msg.send(f"The mentioned role(s) or member(s) were not found\n{opts}")
        for member in opts:
            if isinstance(member,discord.Member):
                found_member=True
                for role in member.roles:
                    if role.id not in remove_roles:
                        new_roles.append(role)
                await member.edit(roles=new_roles)

        if found_member == False:
            for role in msg.author.roles:
                if role.id not in remove_roles:
                    new_roles.append(role)
            await msg.author.edit(roles=new_roles)
        return await msg.message.add_reaction(emoji="✅")


    @commands.has_permissions()
    @command(name='greetmsg')
    async def greetMsg(self,msg,*,message):
        await self.dataCheck(msg)
        if self.localData[str(msg.guild.id)]['greetings']['channel'] is None:
            return await msg.send("Please set a greetings channel first")
        stringCheck= await self.checkEvalString(message)
        if stringCheck[0] is False:
            messageList='\n'.join(stringCheck[1])
            return await msg.send(f"Invalid variable naming, please check the guide below.\n{messageList}")
        if message in self.localData[str(msg.guild.id)]['greetings']['messages']:
            return await msg.send("The greetings message is already in database\nPlease set a different one.")
        
        self.localData[str(msg.guild.id)]['greetings']['messages'].append(message)
        return await msg.send(f"New greetings message added.\n{message}")


    @commands.has_permissions(manage_channels=True)
    @command(name='sgc',aliases=['set-greet-chan','setgreetchan'])
    async def setGreetingsChannel(self,msg,channel:discord.TextChannel=None):
        """
        Sets a channel for sending messages when a new user joins the channel
        If no channel is provided, it will use the current as the channel
        """

        if channel is None:
            channel = msg.channel
        
        self.localData[str(msg.guild.id)]['greetings']['channel']=channel.id
        await msg.send(f"New member join greetings channel has been set to {channel.mention}")

    @commands.has_permissions(ban_members=True)
    @command()
    async def ban(self,msg,*users:discord.Member):
        """
        Ban out the mentioned users
        `Ex:` s.ban @User1 @User2 @User3
        `Permissions:` Ban Members
        `Command:` ban(users:list)
        """
        if not users:
            return await msg.send("Please mention the user(s) to ban from the server")
        
        if users:
            banned=[]
            failed=[]
            for user in users:
                try:
                    await msg.guild.ban(user=user)
                    banned.append(user.name)
                except Exception:
                    failed.append(user.name)

            if banned:
                await msg.send(f"Banned the following members from the server {', '.join(banned)}")

            if failed:
                await msg.send(f"Failed to ban the following members {', '.join(failed)}.\nPlease check for permissions")



    @commands.has_permissions(ban_members=True)
    @command()
    async def unban(self,msg,userId:int):
        try:
            getUser= await self.bot.fetch_user(userId)
            await msg.guild.unban(getUser)
        except discord.NotFound:
            return await msg.send(f"User with ID: {userId} not found")

        except discord.HTTPException:
            return await msg.send(f"Failed to unban user")

        except discord.Forbidden:
            return await msg.send("You lack permission to ban the user")

        return await msg.send(f"user {getUser.name} has been unbanned.")

    @commands.has_permissions(kick_members=True)
    @command(aliases=['boot'])
    async def kick(self,msg,*users:discord.Member):
        """
        Kick out the mentioned users
        `Ex:` s.kick @User1 @User2 @User3
        `Permissions:` Kick Members
        `Command:` kick(users:list)
        """
        if not users:
            return await msg.send("Please enter the name of the user(s) or mention the user(s) to kick from the server or mention them.")

        if users:
            booted=[]
            failed=[]
            for user in users:
                try:
                    await msg.guild.kick(user=user)
                    booted.append(user.name)
                except Exception:
                    failed.append(user.name)

            if booted:
                await msg.send(f"Booted {', '.join(booted)}")

            if failed:
                await msg.send(f"Failed to kick the members {', '.join(failed)}")



    @commands.has_permissions(manage_messages=True)
    @command()
    async def warn(self,msg,user:discord.Member,*,reason):
        await self.dataCheck(msg)
        if str(user.id) in self.localData[str(msg.guild.id)]['warnings']:
            self.localData[str(msg.guild.id)]['warnings'][str(user.id)].append(reason)
            return await msg.send(f"{user.mention}, you have received a warning from {msg.author.name} with reason: {reason}")

        self.localData[str(msg.guild.id)]['warnings'][str(user.id)]=[reason]
        return await msg.send(f"{user.mention}, you have received a warning from {msg.author.name} with reason: {reason}")
        




    @commands.has_permissions()
    @command()
    async def warnings(self,msg,user:discord.Member=None):
        await self.dataCheck(msg)
        if user is None:
            user = msg.author
        
        if str(user.id) in self.localData[str(msg.guild.id)]['warnings']:
            return await msg.send(f"Name: {user.name}\nWarnings: {len(self.localData[str(msg.guild.id)]['warnings'][str(user.id)])}\nMessages: {', '.join(self.localData[str(msg.guild.id)]['warnings'][str(user.id)])}")

        return await msg.send(f"{user.name} has no warnings")



def setup(bot):
    bot.add_cog(Administration(bot))
