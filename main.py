import discord
from discord.ext import commands
import music

cogs = [music]
client = commands.Bot(command_prefix='?', intents = discord.Intents.all())

for i in range(len(cogs)):
  cogs[i].setup(client)


client.run("OTI2MjY4NzE0Mzc3MTc5MTc2.Yc5M9g.YGXyWLOexKJp7t14OZXSD7pwiGU")

