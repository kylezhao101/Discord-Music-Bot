# Discord Music Bot

A music bot written in discord.py using youtube-dl and asyncio.

### Music commands

```
join
  aliases: j, connect
  joins the user's current voice channel
volume <optional value 0-100>
  aliases: v, vol
  display current volume
  changes volume to: volume <0-100>
remove <position>
  aliases: r, rem, rm
  removes song in queue position
queue
  aliases: q, playlist, que
  displays the song queue
nowplaying
  aliases: np, song, current, currentsong, playing
  displays current song
play <search or URL>,
  aliases: p, sing 
  enqueues a song based on key words or a link
  queues a playlist from a link
skip 
  aliases: s, next
  skips to the next song in queue
clear
  aliases: clr, cl, cr
  clears the entire queue
shuffle
  aliases: sf
  randomizes the queue
move <songnumber, newposition>
  aliases: m
    e.g, ??move 5,3 
    e.g. ??move 5 to 3
  moves one song in queue to a specified position
loop
  aliases: l
  toggles the function to keep playing the same song
```
### User-favourite's commands

This bot uses mongodb to store unique user playlists. 
These can be modified and played through discord.

```
favourite <search or URL>
  aliases: f, fav
  Adds a song to the user's favourites list based on the keywords or URL
  playlists are unsupported
favourites
  aliases: fs, favs
  displays user's favourite songs
removefavourite <song number>
  aliases: rf, removefav, remfav
  removes song at index <song number> from the user's favourites
playfavourites <range>
  aliases: pf, playfav
  plays specified songs from favourites list
  <range>
    e.g. ??pf all or ??pf a
      plays all songs on the favourites list
    e.g. ??pf 2
      plays song that matches the index 2
    e.g. ??pf 1,5
      plays all songs from 1 to 5
```
