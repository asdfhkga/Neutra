import subprocess
import asyncio
import asyncpg
import discord
import random
import dis
import math
import os
import io
import sys
import copy
import fnmatch
import time
import importlib
import aiohttp
import datetime
import traceback
import json
import collections
import discord
import asyncio
import aiohttp
import json
import subprocess
from discord.ext.commands import Bot
from random import randint
from discord.ext import commands
from platform import python_version
import os
import re
import datetime
import pytz
import platform



from discord.ext import commands, menus
from utilities import permissions, pagination, converters


def setup(bot):
    bot.add_cog(BotAdmin(bot))


class BotAdmin(commands.Cog):
    """
    Bot admin only stats cog.
    """
    def __init__(self, bot):
        self.bot = bot
        
        self.emote_dict = bot.emote_dict
        self.socket_since = datetime.datetime.utcnow()
        self.socket_event_total = 0

    # This is a bot admin only cog
    async def cog_check(self, ctx):
        if ctx.author.id not in self.bot.constants.admins:
            return
        return True


    @commands.Cog.listener()
    async def on_socket_response(self, msg: dict):
        """When a websocket event is received, increase our counters."""
        if event_type := msg.get("t"):
            self.socket_event_total += 1
            self.bot.socket_events[event_type] += 1


    @commands.command()
    async def socket(self, ctx):
        """Fetch information on the socket events received from Discord."""
        running_s = (datetime.datetime.utcnow() - self.socket_since).total_seconds()

        per_s = self.socket_event_total / running_s

        width = len(max(self.bot.socket_events, key=lambda x: len(str(x))))
        
        line = '\n'.join('{0:<{1}} : {2:>{3}}'.format(
            str(event_type),
            width,
            count,
            len(max(str(count)))
        ) for event_type, count in self.bot.socket_events.most_common())

        header = '**Receiving {0:0.2f} socket events per second** | **Total: {1}**\n'.format(
            per_s,
            self.socket_event_total
        )

        m = pagination.MainMenu(pagination.TextPageSource(line, prefix="```yaml", max_size= 500))
        await ctx.send(header)
        try:
            
            await m.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


    @commands.command(aliases=['pm'], brief="DM the user of your choice", hidden=True)
    @commands.is_owner()
    @commands.check(permissions.is_owner)
    async def dm(self, ctx, user_id: int, *, message: str):
        """ 
        Usage:       -dm <id> <message>
        Alias:       -pm
        Example:     -dm 384059834985989 Hi
        Permissions: Bot Owner
        """
        user = self.bot.get_user(user_id)
        if not user:
            return await ctx.send(f"Could not find any UserID matching **{user_id}**")

        try:
            await user.send(message)
            await ctx.send(f"✉️ Sent a DM to **{user_id}**")
        except discord.Forbidden:
            await ctx.send("This user might be having DMs blocked or it's a bot account...")


    @commands.command(brief="Get me a server invite")
    async def inv(self, ctx, server: converters.BotServer = None):
        """
        Just type a server and get an invite.
        """
        if server is None:
            server = ctx.guild
        if type(server) is list:
            if len(server) > 1:
                msg = ""
                for x in server:
                    guild = self.bot.get_guild(int(x))
                    msg += f"ID: {guild.id} Name: {guild.name}\n"
                await ctx.send(f"Multiple results. Please use the server ID instead")
                t = pagination.MainMenu(pagination.TextPageSource(text=msg, max_size=500))
                try:
                    return await t.start(ctx)
                except menus.MenuError as e:
                    await ctx.send(e)
            else:
                try:
                    server = self.bot.get_guild(int(server[0]))
                except IndexError:
                    return await ctx.send(f"Couldn't find that server.")
        
        s = random.choice(server.text_channels)
        try:
            inv = await s.create_invite()
        except Exception as e:
            return await ctx.send(e)
        await ctx.send(inv)


    @commands.command(brief="server members")
    async def members(self, ctx, *, server: converters.BotServer = None):
        """
        Usage: -members [server]
        """
        if server is None:
            server = ctx.guild
        if type(server) is list:
            if len(server) > 1:
                my_dict = {}
                for x in server:
                    guild = self.bot.get_guild(int(x))
                    my_dict[guild.id] = f"ID: {guild.id} Name: {guild.name}\n"
                the_list = [my_dict[x] for x in my_dict]
                index, message = await pagination.Picker(embed_title="Multiple results. Please choose one.", list=the_list, ctx=ctx).pick(embed=True, syntax="py")
                if index < 0:
                    return await message.edit(content=f"{self.bot.emote_dict['info']} Server selection cancelled.", embed=None)


                key_list = list(my_dict.keys())
                selection = key_list[index]

                try:
                    server = self.bot.get_guild(int(selection))
                except Exception as e:
                    return await ctx.send(f"Couldn't find that server.")
            else:
                try:
                    server = self.bot.get_guild(int(server[0]))
                except IndexError:
                    return await ctx.send(f"Couldn't find that server.")
        members = server.members
        member_list = []
        for entity in members:
            member_list.append(
                {
                    "name":entity,
                    "value":"Mention: {}\nID: `{}`\nNickname: {}".format(entity.mention, entity.id, entity.display_name)
                }
            )
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(member_list)],
            per_page=10,
            title=f"Member list for **{server.name}** ({len(members):,} total)"
        ))
        await message.delete()
        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


    @commands.command(brief="Lists the servers I'm connected to.", aliases=['servers', 'serverlist'])
    async def listservers(self, ctx):
        """Lists the servers I'm connected to."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":guild.name,
                    "value":"{:,} member{}\nID: `{}`".format(len(guild.members),"" if len(guild.members)==1 else "s", guild.id),
                    "users":len(guild.members)
                }
            )
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="Server's I'm Connected To ({:,} total)".format(len(self.bot.guilds)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


    @commands.command(brief="most member servers")
    async def topservers(self, ctx):
        """Lists the top servers I'm connected to ordered by population."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":guild.name,
                    "value":"{:,} member{}".format(len(guild.members),"" if len(guild.members)==1 else "s"),
                    "users":len(guild.members)
                }
            )
        our_list = sorted(our_list, key=lambda x:x["users"],reverse=True)
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="Top Servers By Population ({} total)".format(len(self.bot.guilds)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


    @commands.command(brief="least member servers")
    async def bottomservers(self, ctx):
        """Lists the bottom servers I'm connected to ordered by population."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":guild.name,
                    "value":"{:,} member{}".format(len(guild.members),"" if len(guild.members)==1 else "s"),
                    "users":len(guild.members)
                }
            )
        our_list = sorted(our_list, key=lambda x:x["users"])
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="Bottom Servers By Population ({:,} total)".format(len(self.bot.guilds)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

    @commands.command(brief="first joined servers.")
    async def firstservers(self, ctx):
        """Lists the first servers I've joined."""
        our_list = []
        for guild in self.bot.guilds:
            bot = guild.me
            our_list.append(
                {
                    "name":"{} ({:,} member{})".format(guild.name,len(guild.members),"" if len(guild.members)==1 else "s"),
                    "value":"{} UTC".format(bot.joined_at.strftime("%Y-%m-%d %I:%M %p") if bot.joined_at != None else "Unknown"),
                    "date":bot.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1)
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="First Servers I Joined ({:,} total)".format(len(self.bot.guilds)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


    @commands.command(brief="last joined servers.", aliases=['lastservers'])
    async def recentservers(self, ctx):
        """Lists the most recent users to join - default is 10, max is 25."""
        our_list = []
        for guild in self.bot.guilds:
            bot = guild.me
            our_list.append(
                {
                    "name":"{} ({} member{})".format(guild.name,len(guild.members),"" if len(guild.members)==1 else "s"),
                    "value":"{} UTC".format(bot.joined_at.strftime("%Y-%m-%d %I:%M %p") if bot.joined_at != None else "Unknown"),
                    "date":bot.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1, reverse=True)
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="Most Recent Servers I Joined ({:,} total)".format(len(self.bot.guilds)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

    # Basic info commands
    @commands.command(brief="Commands in the current cache.")
    async def cachedcommands(self, ctx, limit=20):
        counter = self.bot.command_stats
        width = len(max(counter, key=len))
        total = sum(counter.values())

        if limit > 0:
            common = counter.most_common(limit)
        else:
            common = counter.most_common()[limit:]
        output = '\n'.join('{0:<{1}} : {2}'.format(k, width, c)
                           for k, c in common)

        await ctx.send('```yaml\n{}\n```'.format(output))


    @commands.command(aliases=['guildinfo','gi'], brief="Get stats on a bot server.")
    async def guild(self, ctx, *, guild: converters.BotServer = None):
        """Lists some info about the current or passed server."""

        if guild is None:
            try:
                guild = ctx.guild
            except Exception:
                return await ctx.send(f"Couldn't find that server.")
        if type(guild) is list:
            if len(guild) > 1:
                my_dict = {}
                for x in guild:
                    guild = self.bot.get_guild(int(x))
                    my_dict[guild.id] = f"ID: {guild.id} Name: {guild.name}\n"
                the_list = [my_dict[x] for x in my_dict]
                index, message = await pagination.Picker(embed_title="Multiple results. Please choose one.", list=the_list, ctx=ctx).pick(embed=True, syntax="py")
                if index < 0:
                    return await message.edit(content=f"{self.bot.emote_dict['info']} Server selection cancelled.", embed=None)


                key_list = list(my_dict.keys())
                selection = key_list[index]

                try:
                    guild = self.bot.get_guild(int(selection))
                except Exception as e:
                    return await ctx.send(f"Couldn't find that server.")
            else:
                try:
                    guild = self.bot.get_guild(int(guild[0]))
                except IndexError:
                    return await ctx.send(f"Couldn't find that server.")
        server_embed = discord.Embed(color=ctx.guild.me.color)
        server_embed.title = guild.name
        
        # Get localized user time
        local_time = datetime.datetime.utcnow()
        # local_time = UserTime.getUserTime(ctx.author, self.settings, guild.created_at)
        time_str = "{}".format(local_time)
        
        server_embed.description = "Created at {}".format(time_str)
        online_members = 0
        bot_member     = 0
        bot_online     = 0
        for member in guild.members:
            if member.bot:
                bot_member += 1
                if not member.status == discord.Status.offline:
                        bot_online += 1
                continue
            if not member.status == discord.Status.offline:
                online_members += 1
        # bot_percent = "{:,g}%".format((bot_member/len(guild.members))*100)
        user_string = "{:,}/{:,} online ({:,g}%)".format(
                online_members,
                len(guild.members) - bot_member,
                round((online_members/(len(guild.members) - bot_member) * 100), 2)
        )
        b_string = "bot" if bot_member == 1 else "bots"
        user_string += "\n{:,}/{:,} {} online ({:,g}%)".format(
                bot_online,
                bot_member,
                b_string,
                round((bot_online/bot_member)*100, 2)
        )
        #server_embed.add_field(name="Members", value="{:,}/{:,} online ({:.2f}%)\n{:,} {} ({}%)".format(online_members, len(guild.members), bot_percent), inline=True)
        server_embed.add_field(name="Members ({:,} total)".format(len(guild.members)), value=user_string, inline=True)
        server_embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        chandesc = "{:,} text, {:,} voice".format(len(guild.text_channels), len(guild.voice_channels))
        server_embed.add_field(name="Channels", value=chandesc, inline=True)
        server_embed.add_field(name="Default Role", value=guild.default_role, inline=True)
        server_embed.add_field(name="Owner", value=guild.owner.name + "#" + guild.owner.discriminator, inline=True)
        server_embed.add_field(name="AFK Channel", value=guild.afk_channel, inline=True)
        server_embed.add_field(name="Verification", value=guild.verification_level, inline=True)
        server_embed.add_field(name="Voice Region", value=guild.region, inline=True)
        server_embed.add_field(name="Considered Large", value=guild.large, inline=True)
        # server_embed.add_field(name="Shard ID", value="{}/{}".format(guild.shard_id+1, self.bot.shard_count), inline=True)
        server_embed.add_field(name="Nitro Boosts",value="{} (level {})".format(guild.premium_subscription_count,guild.premium_tier))
        # Find out where in our join position this server is
        joinedList = []
        popList    = []
        for g in self.bot.guilds:
            joinedList.append({ 'ID' : g.id, 'Joined' : g.me.joined_at })
            popList.append({ 'ID' : g.id, 'Population' : len(g.members) })
        
        # sort the guilds by join date
        joinedList = sorted(joinedList, key=lambda x:x["Joined"].timestamp() if x["Joined"] != None else -1)
        popList = sorted(popList, key=lambda x:x['Population'], reverse=True)
        
        check_item = { "ID" : guild.id, "Joined" : guild.me.joined_at }
        total = len(joinedList)
        position = joinedList.index(check_item) + 1
        server_embed.add_field(name="Join Position", value="{:,} of {:,}".format(position, total), inline=True)
        
        # Get our population position
        check_item = { "ID" : guild.id, "Population" : len(guild.members) }
        total = len(popList)
        position = popList.index(check_item) + 1
        server_embed.add_field(name="Population Rank", value="{:,} of {:,}".format(position, total), inline=True)
        
        emojitext = ""
        emojifields = []
        disabledemojis = 0
        twitchemojis = 0
        for i,emoji in enumerate(guild.emojis):
            if not emoji.available:
                disabledemojis += 1
                continue
            if emoji.managed:
                twitchemojis += 1
                continue
            emojiMention = "<{}:{}:{}>".format("a" if emoji.animated else "",emoji.name,emoji.id)
            test = emojitext + emojiMention
            if len(test) > 1024:
                # TOOO BIIIIIIIIG
                emojifields.append(emojitext)
                emojitext=emojiMention
            else:
                emojitext = emojitext + emojiMention
        
        if len(emojitext): emojifields.append(emojitext) # Add any leftovers
        if twitchemojis:   emojifields.append("{:,} managed".format(twitchemojis))
        if disabledemojis: emojifields.append("{:,} unavailable".format(disabledemojis)) # Add the disabled if any

        server_embed.set_thumbnail(url=guild.icon_url if len(guild.icon_url) else ctx.author.default_avatar_url)
        server_embed.set_footer(text="Server ID: {}".format(guild.id))
        # Let's send all the embeds we need finishing off with extra emojis as needed
        for i,e in enumerate(emojifields):
            name = "Disabled Emojis" if e.lower().endswith("unavailable") else "Twitch Emojis" if e.lower().endswith("managed") else "Emojis ({} of {})".format(i+1,len(emojifields))
            server_embed.add_field(name=name,value=e,inline=True)
            if len(server_embed) > 6000: # too big
                server_embed.remove_field(len(server_embed.fields)-1)
                await ctx.send(embed=server_embed)
                server_embed = discord.Embed(color=self.bot.constants.embed)
                server_embed.title = guild.name
                server_embed.set_thumbnail(url=guild.icon_url if len(guild.icon_url) else ctx.author.default_avatar_url)
                server_embed.set_footer(text="Server ID: {}".format(guild.id))
                server_embed.description = "Continued Emojis:"
                server_embed.add_field(name=name,value=e,inline=True)
        if len(server_embed.fields):
            try:
                await message.edit(embed=server_embed)
            except:
                await ctx.send(embed=server_embed)

    @commands.command(aliases=['ns'], brief="Get a list of all my nicknames!")
    async def nickscan(self, ctx):
        """Get a list of all my nicknames!"""
        nick = ""
        bool = None
        for guild in self.bot.guilds:
            if len(nick + "**Server:** `{}` **Nick:** `{}`\n".format(guild.name, guild.get_member(self.bot.user.id).nick)) > 2000:
                bool = False
                break
            if guild.get_member(self.bot.user.id).nick:
                nick += "**Server:** `{}` **Nick:** `{}`\n".format(guild.name, guild.get_member(self.bot.user.id).nick)
        if not nick:
            await ctx.send("I have no nicknames set!")
        else:
            if len(nick) <= 1964 and bool == False:
                nick += "**Could not print the rest, sorry.**"
            elif bool == False:
                bool = True
            try:
                embed = discord.Embed(title="Servers I Have Nicknames In", color = ctx.guild.me.color)
                embed.description = nick
                await ctx.send(embed=embed)
            except:
                await ctx.send("```{}```".format(nick))
            if bool == True:
                await ctx.send("**Could not print the rest, sorry.**")


    @commands.command(aliases=['code','cloc'], brief="Gives the number of lines in the source code")
    async def lines(self, ctx):
        """Gives the number of lines in the source code"""
        async with ctx.channel.typing():
        # Script from https://github.com/kyco/python-count-lines-of-code/blob/python3/cloc.py
        
        # Get our current working directory - should be the bot's home
            path = os.getcwd()

            # Set up some lists
            extensions = []
            code_count = []
            include = ['py','sql','json','yml']

            # Get the extensions - include our include list
            extensions = self.get_extensions(path, include)

            for run in extensions:
                extension = "*."+run
                temp = 0
                for root, dir, files in os.walk(path):
                    for items in fnmatch.filter(files, extension):
                        value = root + "/" + items
                        temp += sum(+1 for line in open(value, 'rb'))
                code_count.append(temp)
                pass
            
            # Set up our output
            msg = 'Info on home directory:\n```fix\n'
            padTo = 0
            for idx, val in enumerate(code_count):
                # Find out which has the longest
                tempLen = len(str('{:,}'.format(code_count[idx])))
                if tempLen > padTo:
                    padTo = tempLen
            for idx, val in enumerate(code_count):
                lineWord = 'lines'
                if code_count[idx] == 1:
                    lineWord = 'line'

                numString = str('{:,}'.format(code_count[idx])).ljust(padTo, ' ')
                msg += numString + " " + lineWord + " of " + extensions[idx] + "\n"
                pass
            msg += '```'
            await ctx.send(msg)

    # Helper function to get extensions
    def get_extensions(self, path, excl):
        extensions = []
        for root, dir, files in os.walk(path):
            for items in fnmatch.filter(files, "*"):
                temp_extensions = items.rfind(".")
                ext = items[temp_extensions+1:]
                if ext not in extensions:
                    if ext in excl:
                        extensions.append(ext)
                        pass
        return extensions

    def _get_imports(self, file_name):
        if not os.path.exists("cogs/" + file_name):
            return []
        file_string = open("cogs/" + file_name, "rb").read().decode("utf-8")
        instructions = dis.get_instructions(file_string)
        imports = [__ for __ in instructions if 'IMPORT' in __.opname]
        i = []
        for instr in imports:
            if not instr.opname == "IMPORT_FROM":
                continue
            i.append(instr.argval)
        cog_imports = []
        for f in i:
            if os.path.exists("cogs/" + f + ".py"):
                cog_imports.append(f)
        return cog_imports

    def _get_imported_by(self, file_name):
        ext_list = []
        for ext in os.listdir("cogs"):
            # Avoid reloading Settings and Mute
            if not ext.lower().endswith(".py") or ext == file_name:
                continue
            if file_name[:-3] in self._get_imports(ext):
                ext_list.append(ext)
        return ext_list

    async def _send_embed(self, ctx, embed, pm = False):
        # Helper method to send embeds to their proper location
        if pm == True and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages, try to dm
            try:
                await ctx.send(embed=embed)
                # await ctx.author.send(embed=embed)
                # await ctx.message.add_reaction("📬")
            except discord.Forbidden:
                await ctx.send(embed=embed)
            return
        await ctx.send(embed=embed)

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")
    

    @commands.command(hidden=True, brief="Outputs the cogs attatched to the passed extension")
    async def extension(self, ctx, *, extension = None):
        """Outputs the cogs attatched to the passed extension."""
        if extension == None:
            # run the extensions command
            await ctx.invoke(self.extensions)
            return

        cog_list = []
        for e in self.bot.extensions:
            if not str(e[5:]).lower() == extension.lower():
                continue
            # At this point - we should've found it
            # Get the extension
            b_ext = self.bot.extensions.get(e)
            for cog in self.bot.cogs:
                # Get the cog
                b_cog = self.bot.get_cog(cog)
                if self._is_submodule(b_ext.__name__, b_cog.__module__):
                    # Submodule - add it to the list
                    cog_list.append(str(cog))
            # build the embed
            if type(ctx.author) is discord.Member:
                help_embed = discord.Embed(color=ctx.author.color)
            else:
                help_embed = discord.Embed(color=random.choice(self.colors))
            help_embed.title = str(e[5:]) + " Extension"
            if len(cog_list):
                total_commands = 0
                for cog in cog_list:
                    total_commands += len(self.bot.get_cog(cog).get_commands())
                if len(cog_list) > 1:
                    comm = "total command"
                else:
                    comm = "command"
                if total_commands == 1:
                    comm = "> 1 " + comm
                else:
                    comm = "> {:,} {}s".format(total_commands, comm)
                help_embed.add_field(name=", ".join(cog_list), value=comm, inline=True)
            else:
                help_embed.add_field(name="No Cogs", value="> 0 commands", inline=True)
            await ctx.send(embed=help_embed)
            return
        await ctx.send("I couldn't find that extension.")


    @commands.command(hidden=True, brief="Lists all extensions and their corresponding cogs.")
    async def extensions(self, ctx):
        """Lists all extensions and their corresponding cogs."""
        # Build the embed
        if type(ctx.author) is discord.Member:
            help_embed = discord.Embed(color=ctx.author.color)
        else:
            help_embed = discord.Embed(color=random.choice(self.colors))
            
        # Setup blank dict
        ext_list = {}
        cog_less = []
        for extension in self.bot.extensions:
            if not str(extension)[5:] in ext_list:
                ext_list[str(extension)[5:]] = []
            # Get the extension
            b_ext = self.bot.extensions.get(extension)
            for cog in self.bot.cogs:
                # Get the cog
                b_cog = self.bot.get_cog(cog)
                if self._is_submodule(b_ext.__name__, b_cog.__module__):
                    # Submodule - add it to the list
                    ext_list[str(extension)[5:]].append(str(cog))
            if not len(ext_list[str(extension)[5:]]):
                ext_list.pop(str(extension)[5:])
                cog_less.append(str(extension)[5:])
        
        if not len(ext_list) and not len(cog_less):
            # no extensions - somehow... just return
            return
        
        # Get all keys and sort them
        key_list = list(ext_list.keys())
        key_list = sorted(key_list)
        
        if len(cog_less):
            ext_list["Cogless"] = cog_less
            # add the cogless extensions at the end
            key_list.append("Cogless")
        
        to_pm = len(ext_list) > 24
        page_count = 1
        page_total = math.ceil(len(ext_list)/24)
        if page_total > 1:
            help_embed.title = "Extensions (Page {:,} of {:,})".format(page_count, page_total)
        else:
            help_embed.title = "Extensions"
        for embed in key_list:
            if len(ext_list[embed]):
                help_embed.add_field(name=embed, value="> " + ", ".join(ext_list[embed]), inline=True)
            else:
                help_embed.add_field(name=embed, value="> None", inline=True)
            # 25 field max - send the embed if we get there
            if len(help_embed.fields) >= 24:
                if page_total == page_count:
                    if len(ext_list) == 1:
                        help_embed.set_footer(text="1 Extension Total")
                    else:
                        help_embed.set_footer(text="{} Extensions Total".format(len(ext_list)))
                await self._send_embed(ctx, help_embed, to_pm)
                help_embed.clear_fields()
                page_count += 1
                if page_total > 1:
                    help_embed.title = "Extensions (Page {:,} of {:,})".format(page_count, page_total)
        
        if len(help_embed.fields):
            if len(ext_list) == 1:
                help_embed.set_footer(text="1 Extension Total")
            else:
                help_embed.set_footer(text="{} Extensions Total".format(len(ext_list)))
            await self._send_embed(ctx, help_embed, to_pm)

    @commands.command(brief="Who are the bot admins?")
    async def botadmins(self, ctx):
        our_list = []
        for user_id in self.bot.constants.admins:
            user = await self.bot.fetch_user(user_id)
            our_list.append(
                {
                    "name": f"**{str(user)}**",
                    "value": f"ID: `{user.id}`"
                }
            )
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="My Admins ({:,} total)".format(len(self.bot.constants.admins)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

    @commands.command(brief="Who are the bot owners?", aliases=['owners'])
    async def botowners(self, ctx):
        our_list = []
        for user_id in self.bot.constants.owners:
            user = await self.bot.fetch_user(user_id)
            our_list.append(
                {
                    "name": f"**{str(user)}**",
                    "value": f"ID: `{user.id}`"
                }
            )
        p = pagination.MainMenu(pagination.FieldPageSource(
            entries=[("{}. {}".format(y+1,x["name"]), x["value"]) for y,x in enumerate(our_list)], 
            title="My Owners ({:,} total)".format(len(self.bot.constants.owners)),
            per_page=15))

        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)