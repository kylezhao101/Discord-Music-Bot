import pymongo
from pymongo import MongoClient
import os

import discord
from discord.ext import commands

import random
import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
from collections import deque
from youtube_dl import YoutubeDL
import youtube_dl
import datetime

cluster = MongoClient(os.environ['mongoURL'])
db = cluster["qwiooData"]
collection = db["userData"]

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass

client = commands.Bot(command_prefix='??',
                      intents=discord.Intents.all(),
                      activity=discord.Game(name="music | ??help"))
ytdlopts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class YTDLError(Exception):
  pass

class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""

class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
       
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.thumbnail = data.get('thumbnail') 

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop=None, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        embed = discord.Embed(title="", description=f"Queued [{data['title']}]({data['webpage_url']}) {datetime.timedelta(seconds=(data['duration']))} [{ctx.author.mention}]", color=0xF8C514)
        
        embed.set_thumbnail(url=data['thumbnail'])
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 'duration': str(datetime.timedelta(seconds=(data['duration'])))}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):

        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hr'.format(hours))
        if minutes > 0:
            duration.append('{} min'.format(minutes))
        if seconds > 0:
            duration.append('{} sec'.format(seconds))

        return ', '.join(duration)

class Spotify(commands.Cog):
    def getTrackID(self, track):
        track = sp.track(track)
        return track["id"]
    def getPlaylistTrackIDs(self, playlist_id):
        ids = []
        playlist = sp.playlist(playlist_id)
        for item in playlist['tracks']['items']:
            track = item['track']
            ids.append(track['id'])
        return ids
  

class MusicPlayer(commands.Cog):
    __slots__ = ('bot', '_guild', '_channel', 'voice_client', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel

        self.voice_client = ctx.voice_client  

        self._cog = ctx.cog
        
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self._loop = False
        self.np = None  # Now playing message
        self.volume = .69
        self.current = None
        
        ctx.bot.loop.create_task(self.player_loop())

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    async def player_loop(self):

        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()
            if not self._loop:
              try:
                    # Wait for the next song. If we timeout - cancel the player and disconnect
                    async with timeout(300): 
                        source = await self.queue.get()
              except asyncio.TimeoutError:
                    return self.destroy(self._guild)
            
            if self.loop:
                  self.queue.join(source)

            if not isinstance(source, YTDLSource):
                # regather to prevent stream expiration
                
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source
       
       
            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
          
                
            embed = discord.Embed(title="", description=f"[{source.title}]({source.web_url}) [{source.requester.mention}] \n`{source.duration}`", color=0xF8C514)

            embed.set_author(icon_url=self.bot.user.avatar_url, name=f"Now Playing 🎶")

            embed.set_thumbnail(url=source.thumbnail)
            await self._channel.send(embed=embed)

            await self.next.wait()
            source.cleanup()
            
            self.current = None

     
    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))

class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        
    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    def _playlist(self, search: str):
      """Returns a dict with all Playlist entries"""
      ydl_opts = {
        'ignoreerrors': True,
        'quit': True,
        'source_address': '0.0.0.0'
      }

      with youtube_dl.YoutubeDL(ydl_opts) as ydl:
          playlist_dict = ydl.extract_info(search, download=False)

          playlistTitle = playlist_dict['title']

          playlist = dict()
          for video in playlist_dict['entries']:
              print()

              if not video:
                  print('ERROR: Unable to get info. Coninuing...')
                  continue
              
              for prop in ['id', 'title']:
                  print(prop, '--', video.get(prop))
                  playlist[video.get('title')] = 'https://www.youtube.com/watch?v=' + video.get('id')
        
          return playlist, playlistTitle

    @commands.command(name='join', aliases=['connect', 'j'], invoke_without_subcommand=True)
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title="", description="No channel to join. Please call `,join` from a voice channel.", color=0xF8C514)
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👍')
        await ctx.send(f'**Joined `{channel}`**')
    
    @commands.command(name='loop', aliases=['l'])
    async def _loop(self,ctx):
      player = self.get_player(ctx)
      vc = ctx.voice_client
      if not vc or not vc.is_playing:
            return await ctx.send('Nothing being played at the moment.')
      player.loop = not player.loop
      await ctx.message.add_reaction('✅')
      await ctx.send("Loop is now: " + str(player.loop))


    @commands.command(name='shuffle', aliases=['sf'])
    async def _shuffle(self, ctx):
        #player = self.get_player(ctx)
        player = self.get_player(ctx)

        if len(list(player.queue._queue)) > 1:
          player.queue._queue = random.sample(list(player.queue._queue), len(list(player.queue._queue)))
          player.queue._queue = deque(player.queue._queue)
          print(player.queue._queue)
          await ctx.send("Shuffled queue")
          await ctx.invoke(self.queue_info)
          
        else:
          await ctx.send("Empty Queue or queue size is 1.")

    @commands.command(name='play', aliases=['sing','p'])
    async def play_(self, ctx, *, search: str):
        
        
        playlist = 0
        await ctx.trigger_typing()
        player = self.get_player(ctx)
        
        vc = ctx.voice_client
        
        if not vc:
            await ctx.invoke(self.connect_)

        #check if link is a playlist
        # if search link has spotify in it        
          
        if search.__contains__('&list='):
          playlist = 1
          await ctx.send('retrieving playlist...')
          async with ctx.typing():
            playlist, playlistTitle = self._playlist(search)
            for _title, _link in playlist.items():
                try:
                    source = await YTDLSource.create_source(ctx, _link, loop=self.bot.loop)
                    await player.queue.put(source)

                except YTDLError as e:
                    await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                    
            await ctx.send(f'Enqueued `{playlist.__len__()}` songs from **{playlistTitle}**')
        
        #continue as usual
        player = self.get_player(ctx)
        if playlist == 1:
          pass
        elif playlist == 0:
          source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
          await player.queue.put(source)

    @commands.command(name='pause')
    async def pause_(self, ctx):  
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title="", description="I am currently not playing anything", color=0xF8C514)
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send("Paused ⏸️")

    @commands.command(name='resume')
    async def resume_(self, ctx):       
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send("Resuming ⏯️")
      
    @commands.command(name='skip', aliases=['next','s'])
    async def skip_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
            
    #TO DO
    #better error handling
    #command to add specific favs to queue
    #command to clear favourites
    @commands.command(name = 'favourite', aliases = ['f', 'fav'])
    async def favourite_(self, ctx, *, search):
        
        
        user = ctx.author
        myquery = { "_id": user.id}
            
        ydl_opts = {
          'format': 'bestaudio', 'noplaylist':'True'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
          data = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        print(data)
        dict = {
            'title': data['title'],
            'webpage_url': data['webpage_url'],
            'duration': str(datetime.timedelta(seconds=(data['duration'])))
          }    
        print(dict)
        try:
          if (collection.count_documents(myquery) == 0):
            post = {"_id": user.id, "favourite": [dict]}
            collection.insert_one(post)
                    
          else:
            collection.update_one({'_id' :user.id}, {"$push" : {'favourite': dict}})
          
          await ctx.channel.send("Added "+ data['title'] +  " to favourites")
        except discord.ext.commands.errors.MissingRequiredArgument:
          await ctx.channel.send("Include song after command")

  
    @commands.command(name = 'favourites', aliases = ['fs', 'favs'])
    async def favourites_(self, ctx):
        user = ctx.author
        myquery = { "_id": user.id }
        x = collection.find_one(myquery)

        try:
          favs = x['favourite']
          fmt = '\n'.join(f"`{(favs.index(_))}.` [{_['title']}]({_['webpage_url']}) | ` {_['duration']} `\n" for _ in favs)
          
          embed=discord.Embed(title="Favourites", description=fmt, color=0xF8C514)  
          embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
          await ctx.send(embed=embed)
          
        except TypeError as e:
          await ctx.send(e)
          
    @commands.command(name= 'removefavourite', aliases = ['rf', 'removefav', 'remfav'])   
    async def removeFavourite_(self,ctx, pos : int=None):
      """Removes specified song from user's favourites"""
      user = ctx.author
      myquery = { "_id": user.id}

      #check if user exists in database
      if (collection.count_documents(myquery) > 0):
  
        x = collection.find_one(myquery)
        favs = x['favourite']

        try:
          await ctx.channel.send("removed " + str(favs[pos]['title']))
          del favs[pos]
          collection.replace_one({'_id' :user.id}, {'favourite': favs})
          
        except IndexError as e:
          await ctx.channel.send(e)
          
      else:
        await ctx.channel.send("use ??f to favourite songs")

    @commands.command(name='playfavourites', aliases=['pf','playfav'])
    async def play_favourites_(self,ctx,*, range):
        user = ctx.author
        myquery = { "_id": user.id}

      #check if user exists in database
        if (collection.count_documents(myquery) > 0):
          try:
            x = collection.find_one(myquery)
            favs = x['favourite'] 
          
            if range == 'all' or range == 'a':
              to_play = favs
            elif ',' in range:
              start, stop = range.split(',')
              
              to_play = favs[int(start) : (int(stop)+1)]
                            
            elif len(str(range)) >= 1:
              
              to_play = favs[(int(range)) : (int(range)+1)]
              print(to_play)
        
            for song in to_play:
              print(song)
              link = song['webpage_url']
              print(type(link))
              
              await ctx.invoke(self.bot.get_command('play'), search = link)

          except ValueError as e:
            await ctx.channel.send(e)
          
        else:
          await ctx.channel.send("use ??f to favourite songs")
#--------------------------------------------------------------------------------

  
    @commands.command(name='remove', aliases=['rm', 'rem', 'r'])
    async def remove_(self, ctx, pos : int=None):
        """Removes specified song from queue"""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos == None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos-1]
                del player.queue._queue[pos-1]
                embed = discord.Embed(title="", description=f"Removed [{s['title']}]({s['webpage_url']}) [{s['requester'].mention}]", color=0xF8C514)
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title="", description=f'Could not find a track for "{pos}"', color=0xF8C514)
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['clr', 'cl', 'cr'])
    async def clear_(self, ctx):
        """Deletes entire queue of upcoming songs."""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('💣 **Cleared**')

    @commands.command(name='queue', aliases=['q', 'playlist', 'que'])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title="", description="queue is empty", color=0xF8C514)
            return await ctx.send(embed=embed)

        print(player.queue._queue)
        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))

        fmt = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {_['duration']} Requested by: {_['requester']}`\n" for _ in upcoming)
        
        fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | ` {vc.source.duration} Requested by: {vc.source.requester}`\n\n__Up Next:__\n" + fmt + f"\n**{len(upcoming)} songs in queue**"

        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=0xF8C514)
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name='np', aliases=['song', 'current', 'currentsong', 'playing'],invoke_without_command=True)
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title="", description="I am currently not playing anything", color=0xF8C514)
            return await ctx.send(embed=embed)
        
               
        embed = discord.Embed(title="", description=f"[{vc.source.title}]({vc.source.web_url}) [{vc.source.requester.mention}]\n`{vc.source.duration}`", color=0xF8C514)
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f"Now Playing 🎶")
        embed.set_image(url=vc.source.thumbnail)
        msg = await ctx.send(embed=embed)

        first_run = True
        while True:
            if first_run:
              reactmoji = ["⏸","▶️","⏩","🎶",'🔊']
              for react in reactmoji:
                          await msg.add_reaction(react)

              def check_react(reaction, user):
                      if reaction.message.id != msg.id:
                          return False
                      if user != ctx.message.author:
                          return False
                      if str(reaction.emoji) not in reactmoji:
                          return False
                      return True
              try:
                      res, user = await self.bot.wait_for('reaction_add', check=check_react)
              except asyncio.TimeoutError:
                      return await msg.clear_reactions()

              if '⏸' in str(res.emoji):
                      print('<<paused>>')
                      ctx.voice_client.pause()
                      
              elif '▶️' in str(res.emoji):
                      print('<<resumed>>')
                      ctx.voice_client.resume()

              elif '⏩' in str(res.emoji):
                      print('<<skipped>>')                      
                      if not vc or not vc.is_connected():
                          embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
                          return await ctx.send(embed=embed)

                      if vc.is_paused():
                          pass
                      elif not vc.is_playing():
                          return

                      vc.stop()     

              elif '🎶' in str(res.emoji):
                      print('<<Displaying queue>>')                      
                      await ctx.invoke(self.queue_info)

              elif '🔊' in str(res.emoji):
                      print('<<Displaying volume>>')                      
                      await ctx.invoke(self.change_volume)             

                    
    @commands.command(name='volume', aliases=['vol', 'v'])
    async def change_volume(self, ctx, *, vol: float=None):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I am not currently connected to voice", color=0xF8C514)
            return await ctx.send(embed=embed)
        
        if not vol:
            embed = discord.Embed(title="", description=f"🔊 **{(vc.source.volume)*100}%**", color=0xF8C514)
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(title="", description="Please enter a value between 1 and 100", color=0xF8C514)
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="", description=f'**`{ctx.author}`** set the volume to **{vol}%**', color=0xF8C514)
        await ctx.send(embed=embed)

    @commands.command(name='leave', aliases=["stop", "dc", "disconnect", "bye"])
    async def leave_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=0xF8C514)
            return await ctx.send(embed=embed)

        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👋')
        await ctx.send('**Successfully disconnected**')

        await self.cleanup(ctx.guild)
    

      
def setup(bot):
    bot.add_cog(Music(bot))
