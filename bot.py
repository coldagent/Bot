import asyncio
import discord
from discord.ext import commands
import yt_dlp

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

# Create bot instance and set command prefix
bot = commands.Bot(command_prefix='`', intents=discord.Intents.all())

# Create a list to store the queued songs
song_queue = []

# Function to play music
async def play_music(ctx: commands.Context):
    if len(song_queue) == 0:
        await ctx.send("The queue is empty. Add some songs using the `play command.")
        return
    
    # Connect to voice channel
    if discord.utils.get(bot.voice_clients, guild=ctx.guild) == None:
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()
    else:
        return

    while song_queue:
        # Get the first song from the queue
        song_info = song_queue[0]

        # Play the song
        ffmpeg_options = {'options': '-vn', "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"}
        await ctx.send(f'**Now playing**: {song_info["fulltitle"]}')
        voice_client.play(discord.FFmpegPCMAudio(song_info["url"], **ffmpeg_options))

        # Wait for the song to finish playing
        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(1)
        song_queue.pop(0)

    # Disconnect from the voice channel once all songs are played
    await voice_client.disconnect()

# Bot event: on ready
@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

# Bot command: queue
@bot.hybrid_command()
async def queue(ctx: commands.Context):
    if len(song_queue) <= 1:
        await ctx.send("The queue is empty. Add some songs using the `play command.")
    else:
        songs = "**Queue:**\n"
        for song_info in song_queue[1:]:
            songs += "\t•\t`" + song_info["fulltitle"] + "`\n"
        await ctx.send(songs)

# Bot command: play
@bot.hybrid_command()
async def play(ctx: commands.Context, url=""):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You are not connected to a voice channel.")
        return
    
    if url != "":
        # Download the song using yt_dlp
        ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192',}],}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            song_queue.append(info)
            await ctx.send(f'**Song queued**: {info["fulltitle"]}')
    elif discord.utils.get(bot.voice_clients, guild=ctx.guild).is_paused():
        await ctx.send("**Resuming**")
        discord.utils.get(bot.voice_clients, guild=ctx.guild).resume()
        return


    await play_music(ctx)

# Bot command: skip
@bot.hybrid_command()
async def skip(ctx: commands.Context):
    voice_client: discord.VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client == None or not voice_client.is_playing():
        await ctx.send("Not playing!")
        return
    await ctx.send("**Skipping**")
    voice_client.stop()

# Bot command: pause
@bot.hybrid_command()
async def pause(ctx: commands.Context):
    voice_client: discord.VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client == None or not voice_client.is_playing():
        await ctx.send("Not playing!")
        return
    await ctx.send("**Pausing**")
    voice_client.pause()

@bot.hybrid_command()
async def sync(ctx: commands.Context):
  if not ctx.author.id == 267094644452491264:
    await ctx.send("You do not have access to this command.")
    return
  fmt = await bot.tree.sync()
  await ctx.send(f"Sync'd {len(fmt)} commands to the current server")

def get_token():
    token = ""
    with open('token.txt', mode='r') as file:
        token = file.read()
    return token

# Run the bot
bot.run(token=get_token())