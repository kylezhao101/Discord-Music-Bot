import discord
from discord.ext import commands
import youtube_dl
import asyncio
import datetime

# removes error message
youtube_dl.utils.bug_reports_message = lambda: ''

# Global variables and options -----------------------------------------------------
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {
  'format':"bestaudio", 
  'source_address': '0.0.0.0'
}

video_id = ""
video_title = ""
length = 0
thumbnail = ""
currentsong = ""
opus_url = ""

#url queue
queue = []

#title queue
title_queue = []

loop = False

#----------------------------------------------------------------------------------------
ytdl = youtube_dl.YoutubeDL(YDL_OPTIONS)

def songdata(url):
  with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
    global video_title
    global length
    global thumbnail

    info = ydl.extract_info(url, download=False)

    length = info['duration']
    video_title = info.get('title', None)
    thumbnail = info.get('thumbnail', None)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
          
      
        filename = data['url'] if stream else ytdl.prepare_filename(data)

        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

#----------------------------------------------------------------------------------------

class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="queue", aliases=['q'])
  async def queue(self, ctx, *, url):
    global queue
    global title_queue
    songdata(url)
    global video_title
  
    queue.append(url)
    title_queue.append(video_title)
    
    em = discord.Embed(title = "**Added to Queue:**", description = video_title, color=0xF8C514)
    await ctx.send(embed = em) 

  @commands.command(name="play", aliases=['p'])
  async def play(self, ctx):
   
    global queue
    global title_queue
    global video_title
    global length
    global thumbnail
    global currentsong
    # needs to reset after song finishes

    if ctx.author.voice is None:
          await ctx.send("You're not in a vc")
        
    voice_channel = ctx.author.voice.channel
        
    if ctx.voice_client is None: 
          #if bot is not in a voice channel
          await voice_channel.connect()
    
    else:
          # if bot is in a voice channel but needs to move over
          await ctx.voice_client.move_to(voice_channel)

    while queue:
      try:
        while voice_channel.is_playing() or voice_channel.is_paused():
          await asyncio.sleep(2)
          pass 
      except AttributeError:
        pass
    
      try:
        async with ctx.typing():
          player = await YTDLSource.from_url(queue[0], loop=self.bot.loop, stream=True)
          ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
          currentsong = queue[0] + " " + video_title
          if loop:
            queue.append(queue[0])
            title_queue.append(title_queue[0])

          del(queue[0]), title_queue[0]

          #create new function for this::
          em = discord.Embed(title = "**Now Playing**", description = video_title, color=0xF8C514)
          em.add_field(name = "**Link**", value = str(queue[0]))
          em.add_field(name = "Duration", value = str(datetime.timedelta(seconds=length)))
          em.set_image(url=thumbnail)
          await ctx.send(embed = em)    

      except:
        break
      
  @commands.command()
  async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")


#-JOIN AND DC-------------------------------------------------------------------------

  @commands.command(name="join", aliases=["j"])
  async def join(self,ctx):

    #if You're not in a voice channel
    if ctx.author.voice is None:
        await ctx.send("You're not in a vc")
    voice_channel = ctx.author.voice.channel

    #if bot is not in a voice channel
    if ctx.voice_client is None: 
        await voice_channel.connect()
    # if bot is in a voice channel but needs to move over
    else:
        await ctx.voice_client.move_to(voice_channel)

  @commands.command(name="disconnect", aliases=["dc"])
  async def disconnect(self,ctx):
    await ctx.voice_client.disconnect()

# QUEUE AND LOOPS --------------------------------------------------------------------

  @commands.command(name='loop', aliases=["l"])
  async def loop(self,ctx):
    global loop

    if loop:
      await ctx.send('Loop mode is off')
      loop = False
    else:
      await ctx.send('Loop mode is on')
      loop = True

  @commands.command(name='remove', aliases=["r"])
  async def remove(self,ctx, number):
    global queue
    global title_queue

    try:
        del(queue[int(number)])
        del(title_queue[int(number)])

        em = discord.Embed(title = "**Queue**", description = ',\n'.join(title_queue), color=0xF8C514)
        await ctx.send(embed = em)   
  
    except:
        await ctx.send('Your queue is either **empty** or the index is **out of range**')

  @commands.command(name='view', aliases=["v"])
  async def view(self,ctx):
    global title_queue

    em = discord.Embed(title = "**Current Queue: **\n", description = '\n'.join(title_queue), color=0xF8C514)
    await ctx.send(embed = em)

  @commands.command(name='nowplaying', aliases=["np"])
  async def np(self,ctx):
    global currentsong
    em = discord.Embed(title = "**Current Song:**", description = currentsong, color=0xF8C514)
    await ctx.send(embed = em)

  @commands.command(name='skip', aliases=["s"])
  async def skip(self,ctx):
    global queue
    global title_queue
    ctx.voice_client.stop()

    del(queue[0])
    del(title_queue[0])
    
# Pause and resume----------------------------------------------------------------------

  @commands.command(name="pause")
  async def pause(self,ctx):
    ctx.voice_client.pause()
    await ctx.send("paused")

  @commands.command(name="resume")
  async def resume(self,ctx):
    ctx.voice_client.resume()
    await ctx.send("resumed")



def setup(client):
  client.add_cog(music(client))