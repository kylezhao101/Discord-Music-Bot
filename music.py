import discord
from discord.ext import commands
import youtube_dl
from youtube_dl import YoutubeDL
import datetime

youtube_dl.utils.bug_reports_message = lambda: ''


# Global variables and options -----------------------------------------------------
queue = []
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format':"bestaudio"}

video_id = ""
video_title = ""
length = 0

#-----------------------------------------------------------------------------------

def songdata(url):
  global video_id
  global video_title
  global length
  length = 0
  youtube_dl_opts = {}
  video = url
  with YoutubeDL(youtube_dl_opts) as ydl:
        info_dict = ydl.extract_info(video, download=False)
        video_id = info_dict.get("id", None)
        video_title = info_dict.get('title', None)
        length += info_dict['duration']

# JOIN and DISCONNECT-------------------------------------------------------------
class music(commands.Cog):
  
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

# QOL Options ------------------------------------------------------------------------

  @commands.command(name='remove', aliases=["r"])
  async def remove(self,ctx, number):
    global queue

    try:
        del(queue[int(number)])
        await ctx.send(f'Your queue is now `{queue}!`')
    
    except:
        await ctx.send('Your queue is either **empty** or the index is **out of range**')

  @commands.command(name='view', help='This command shows the queue')
  async def view(self,ctx):
    global queue
    await ctx.send(f'Your queue is now `{queue}!`')


# QUEUE ----------------------------------------------------------------------------
# url is temp 
# change to song title and info

  @commands.command(name='queue', aliases=["q"])
  async def queue(self,ctx,url):
    queue.append(url)
    await ctx.send(f'`{url}` added to queue!')
    print("current q: "+ queue)

# PLAY ----------------------------------------------------------------------------
  @commands.command(name='play', aliases=["p"])
  async def play(self,ctx,url):
    #join vc
    if ctx.author.voice is None:
        await ctx.send("You're not in a vc")
    voice_channel = ctx.author.voice.channel

    #if bot is not in a voice channel
    if ctx.voice_client is None: 
        await voice_channel.connect()
    # if bot is in a voice channel but needs to move over
    else:
        await ctx.voice_client.move_to(voice_channel)

    global YDL_OPTIONS 
    global FFMPEG_OPTIONS
    global queue
    global video_id
    global video_title
    global length

    songdata(url)
    vc = ctx.voice_client

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(url, download=False)

          url2 = info['formats'][0]['url']
      
          #Plays source audio into the voice channel
          source = await discord.FFmpegOpusAudio.from_probe(url2,**FFMPEG_OPTIONS)
          vc.play(source)

    em = discord.Embed(title = "**Now Playing**", description = video_title, color=0xF8C514)
    em.add_field(name = "**Channel**", value = str(url))
    em.add_field(name = "Duration", value = str(datetime.timedelta(seconds=length)))
    

    #add skip and loop emote functions
    await ctx.send(embed = em)
    

  @commands.command(name='skip', aliases=["s"])
  async def skip(self,ctx):
    global queue
    ctx.voice_client.stop()

    #play next song in q
    del(queue[0])


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