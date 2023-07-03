import asyncio
import discord
from discord.ext import commands
import yt_dlp

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
    
    # Suppress noise about console usage from errors
    yt_dlp.utils.bug_reports_message = lambda: ''

    # Function to play music
    async def play_music(self, ctx: commands.Context):
        if len(self.song_queue) == 0:
            await ctx.send("The queue is empty. Add some songs using the **`play** command.")
            return
        
        # Connect to voice channel
        if discord.utils.get(self.bot.voice_clients, guild=ctx.guild) == None:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            return

        while self.song_queue:
            # Get the first song from the queue
            song_info = self.song_queue[0]

            # Play the song
            ffmpeg_options = {'options': '-vn', "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"}
            await ctx.send(f'**Now playing**: {song_info["fulltitle"]}')
            voice_client.play(discord.FFmpegPCMAudio(song_info["url"], **ffmpeg_options))

            # Wait for the song to finish playing
            while voice_client.is_playing() or voice_client.is_paused():
                await asyncio.sleep(1)
            self.song_queue.pop(0)

        # Disconnect from the voice channel once all songs are played
        await voice_client.disconnect()

    # Bot command: queue
    @commands.hybrid_command()
    async def queue(self, ctx: commands.Context):
        """Displays the current song queue"""

        if len(self.song_queue) <= 1:
            await ctx.send("The queue is empty. Add some songs using the `play command.")
        else:
            songs = "**Queue:**\n"
            for song_info in self.song_queue[1:]:
                songs += "\t•\t`" + song_info["fulltitle"] + "`\n"
            await ctx.send(songs)

    # Bot command: play
    @commands.hybrid_command()
    async def play(self, ctx: commands.Context, arg=""):
        """Plays the given Youtube URL, searches Youtube for audio, or resumes if paused"""

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You are not connected to a voice channel.")
            return
        
        if arg != "":
            # Download the song using yt_dlp
            if "playlist" in arg:
                    await ctx.send("No support for playlists")
                    return
            ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192',}],}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if "www.youtube.com" in arg:
                    info = ydl.extract_info(arg, download=False)
                    self.song_queue.append(info)
                    if len(self.song_queue) > 1:
                        await ctx.send(f'**Song queued**: {info["fulltitle"]}')
                else:
                    await ctx.send("***Searching...***")
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
                    self.song_queue.append(info)
                    if len(self.song_queue) > 1:
                        await ctx.send(f'**Song queued**: {info["fulltitle"]}')
        elif discord.utils.get(self.bot.voice_clients, guild=ctx.guild).is_paused():
            await ctx.send("**Resuming**")
            discord.utils.get(self.bot.voice_clients, guild=ctx.guild).resume()
            return


        await self.play_music(ctx)

    # Bot command: skip
    @commands.hybrid_command()
    async def skip(self, ctx: commands.Context):
        """Skips the current song"""

        voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None or not voice_client.is_playing():
            await ctx.send("Not playing!")
            return
        await ctx.send("**Skipping**")
        voice_client.stop()

    # Bot command: pause
    @commands.hybrid_command()
    async def pause(self, ctx: commands.Context):
        """Pauses the current song"""

        voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None or not voice_client.is_playing():
            await ctx.send("Not playing!")
            return
        voice_client.pause()
        await ctx.send("**Paused**")

async def setup(bot):
    await bot.add_cog(Music(bot))
