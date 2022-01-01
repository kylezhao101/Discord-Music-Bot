import discord
from discord.ext import commands
import os
from discord import Color

import music

cogs = [music]
client = commands.Bot(command_prefix='??', intents = discord.Intents.all(), activity = discord.Game(name="music I ??help"))
client.remove_command("help")

# Custom Help commands ------------------------------------------------------------------

@client.group(invoke_without_command=True, aliases=["h"])
async def help(ctx):
  em = discord.Embed(title = "Help", description = "Use ??help <command> for extended info", color=0xF8C514)
  em.add_field(name = "Music", value = "remove,queue,play,pause,resume")
  await ctx.send(embed = em)
  
@help.command()
async def remove(ctx):
  em = discord.Embed(title = "remove", description = "removes a song from queue", color=0xF8C514)
  em.add_field(name = "**Syntax**", value = "??remove [position], with position starting from 0")
  await ctx.send(embed = em)

@help.command()
async def play(ctx):
  em = discord.Embed(title = "play", description = "plays this song", color=0xF8C514)
  em.add_field(name = "**Syntax**", value = "??play [link or words]")
  await ctx.send(embed = em)

@help.command()
async def queue(ctx):
  em = discord.Embed(title = "queue", description = "Adds this song to queue", color=0xF8C514)
  em.add_field(name = "**Syntax**", value = "??queue [link or words]")
  await ctx.send(embed = em)


for i in range(len(cogs)):
  cogs[i].setup(client)

my_secret = os.environ['qwiootoken']
client.run(my_secret)
