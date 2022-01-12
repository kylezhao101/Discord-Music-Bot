
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

# Custom Help commands ------------------------------------------------------------------
client.remove_command("help")


@client.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title="help",
                       description="Use ??help <command> for extended info",
                       color=0xF8C514)
    em.add_field(name="Music",
                 value="volume,remove,queue,nowplaying,play,skip,clear")

    await ctx.send(embed=em)


@help.command()
async def remove(ctx):
    em = discord.Embed(title="remove",
                       description="removes a song from queue",
                       color=0xF8C514)
    em.add_field(name="**Syntax**",
                 value="??remove [position], with position starting from 1")
    await ctx.send(embed=em)


@help.command()
async def play(ctx):
    em = discord.Embed(title="play", description="plays song", color=0xF8C514)
    em.add_field(name="**Syntax**", value="??play [link or words]")
    await ctx.send(embed=em)


@help.command()
async def queue(ctx):
    em = discord.Embed(
        title="queue",
        description="Displays the current song, as well as queue",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??queue")
    await ctx.send(embed=em)


@help.command()
async def nowplaying(ctx):
    em = discord.Embed(
        title="now playing",
        description="Displays the current song",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??queue")
    await ctx.send(embed=em)


@help.command()
async def clear(ctx):
    em = discord.Embed(
        title="clear",
        description="Resets the entire queue",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??clear")
    await ctx.send(embed=em)    

@help.command()
async def skip(ctx):
    em = discord.Embed(
        title="skip",
        description="skips the current song",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??skip")
    await ctx.send(embed=em)

@help.command()
async def volume(ctx):
    em = discord.Embed(
        title="volume",
        description="Displays the current volume, or sets the volume",
        color=0xF8C514)
    em.add_field(name="**Syntax**", value="??volume [(value 0 - 100)]")
    await ctx.send(embed=em)
#-----------------------------------------------------------------------------------------
for i in range(len(cogs)):
    cogs[i].setup(client)

my_secret = os.environ['qwiootoken']
client.run(my_secret)
