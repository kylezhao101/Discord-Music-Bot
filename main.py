import discord
from discord.ext import commands
import os
import music

cogs = [music]
client = commands.Bot(command_prefix='??',
                      intents=discord.Intents.all(),
                      activity=discord.Game(name="music | ??help"))

@client.event
async def on_ready():
    print("Bot is ready.")
    

#------------------------------------------------------------------

client.remove_command("help")

@client.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title="help",
                       description="Use ??help <command> for extended info",
                       color=0xF8C514)
    em.add_field(name="Music",                    value="join,volume,remove,queue,nowplaying,play,skip,clear,shuffle")
  
    em.add_field(name="**User Favourites**",
                 value="favourite, favourites, removefavourite, playfavourites")
    
    await ctx.send(embed=em)


@help.command()
async def favourite(ctx):
    em = discord.Embed(title="favourite",
                       description="adds a song to your favourites list",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??favourite")
    em.add_field(name="**Aliases**",
                 value="f, fav")
    await ctx.send(embed=em)


@help.command()
async def favourites(ctx):
    em = discord.Embed(title="favourites",
                       description="shows your favourite songs",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??favourites")
    em.add_field(name="**Aliases**",
                 value="fs, favs")
    await ctx.send(embed=em)  
  
@help.command()
async def removefavourite(ctx):
    em = discord.Embed(title="removefavourite",
                       description="removes song from favourites",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??removefavourite [song index starting at 0]")
    em.add_field(name="**Aliases**",
                 value="rf, removefav, remfav")
    await ctx.send(embed=em) 
  
@help.command()
async def playfavourites(ctx):
    em = discord.Embed(title="playfavourites",
                       description="plays songs from favourites list \n e.g. ??pf all, ??pf 2, ??pf 0, 2",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??playfavourites [range], range could be <all> to play every song, or a <specific number> for a certain song on your list, or a range of songs specified by <numOne, numTwo>")
    
    em.add_field(name="**Aliases**",
                 value="pf, playfav")
    await ctx.send(embed=em)

@help.command()
async def join(ctx):
    em = discord.Embed(title="join",
                       description="joins your vc",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??join")
    em.add_field(name="**Aliases**",
                 value="j, connect")
    await ctx.send(embed=em)


@help.command()
async def remove(ctx):
    em = discord.Embed(title="remove",
                       description="removes a song from queue",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??remove [position], with position starting from 1")
    em.add_field(name="**Aliases**",
                 value="r, rem, rm")
    await ctx.send(embed=em)


@help.command()
async def play(ctx):
    em = discord.Embed(title="play", description="plays song, you can search specific songs, or link a playlist", color=0xF8C514)
    em.add_field(name="**Syntax**", value="??play [link or words]")
    em.add_field(name="**Aliases**",
                 value="p, sing")
    await ctx.send(embed=em)


@help.command()
async def queue(ctx):
    em = discord.Embed(
        title="queue",
        description="Displays the current song, as well as queue",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??queue")
    em.add_field(name="**Aliases**",
                 value="q, playlist, que")
    await ctx.send(embed=em)


@help.command()
async def nowplaying(ctx):
    em = discord.Embed(
        title="now playing",
        description="Displays the current song",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??np")
    em.add_field(name="**Aliases**",
                 value="song, current, currentsong, playing")
    await ctx.send(embed=em)


@help.command()
async def clear(ctx):
    em = discord.Embed(
        title="clear",
        description="Resets the entire queue",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??clear")
    em.add_field(name="**Aliases**",
                 value="clr, cl, cr")
    await ctx.send(embed=em)    

@help.command()
async def skip(ctx):
    em = discord.Embed(
        title="skip",
        description="skips the current song",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??skip")
    em.add_field(name="**Aliases**",
                 value="s, next")
    await ctx.send(embed=em)

@help.command()
async def volume(ctx):
    em = discord.Embed(
        title="volume",
        description="Displays the current volume, or sets the volume",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??volume [(value 0 - 100)]")
    em.add_field(name="**Aliases**",
                 value="v, vol")
    await ctx.send(embed=em)

@help.command()
async def shuffle(ctx):
    em = discord.Embed(
        title="shuffle",
        description="Randomizes the queue",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??shuffle")
    em.add_field(name="**Aliases**",
                 value="sf")
    await ctx.send(embed=em)

#-----------------------------------------------------------------------------------------

for i in range(len(cogs)):
    cogs[i].setup(client)

my_secret = os.environ['qwiootoken']
client.run(my_secret)
