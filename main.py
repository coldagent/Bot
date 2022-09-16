import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import field
import os
import discord
from discord.ext import commands
import youtube

f = open("key.txt", "r")
token = f.readline()
f.close()

description = '''A cool bot created by coldagent.'''

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='`', description=description, intents=intents)
song_queue = []  # song_queue for YouTube URLs


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def join(ctx: commands.Context):
    """Joins the same voice channel as the user."""

    if ctx.message.author.voice is None:
        await ctx.send(f'You are not in a Voice Channel!')
        return
    
    vc = ctx.message.author.voice.channel
    await vc.connect()

@bot.command()
async def leave(ctx: commands.Context):
    """Leaves Current Voice Channel."""
    if (not ctx.voice_client == None):
        await ctx.voice_client.disconnect()
        return
    await ctx.send("Not in a voice channel!")

@bot.command()
async def play(ctx: commands.Context, url=None):
    """Plays a YouTube URL in Voice Channel"""
    
    try:
        if (url != None):
            await ctx.send(':mag_right: **Searching for** ``{}``'.format(url))
            player = await youtube.YTDLSource.from_url(url, loop=bot.loop, stream=True)

            if (len(song_queue) < 1):
                song_queue.append(player)
                loop = asyncio.get_event_loop()
                loop.create_task(player_helper(ctx, True))
            else:
                song_queue.append(player)
                await ctx.send(':ballot_box_with_check: **Added to Queue:** ``{}``'.format(player.title))
        elif (len(song_queue) == 0):
            await ctx.send("There is no song to play!.")
        else:
            ctx.voice_client.resume()
            await ctx.send(f":arrow_forward:**Now Playing:** ``{song_queue[0].title}``")

    except Exception as e:
        print(e)
        await ctx.send("Somenthing went wrong - please try again later!")
    
async def player_helper(ctx: commands.Context, first=False):
    if not first:
        delete_top()
    if (len(song_queue) < 1):
        return
    try:
        await ctx.send(f":arrow_forward:**Now Playing:** ``{song_queue[0].title}``")
        loop = asyncio.get_event_loop()
        ctx.voice_client.play(song_queue[0], after=lambda e: loop.create_task(player_helper(ctx)))
    except Exception as e:
        print(str(e))

def delete_top():
    filename = song_queue[0].filename
    song_queue.pop(0)
    if (os.path.exists(filename)):
        os.remove(filename)

@bot.command()
async def skip(ctx: commands.Context):
    """Skips Song Currently Playing"""
    if (ctx.voice_client == None or not ctx.voice_client.is_playing):
        await ctx.send("No song currently playing.")
    else:
        ctx.voice_client.stop()
        await ctx.send(":fast_forward: **Skipped**")

@bot.command()
async def pause(ctx: commands.Context):
    """Pauses the Current Song"""
    if (not ctx.voice_client == None and ctx.voice_client.is_playing()):
        ctx.voice_client.pause()
        await ctx.send(":pause_button: **Pausing the Song**")
    else:
        await ctx.send("There is no song to pause!")

@bot.command()
async def queue(ctx: commands.Context):
    """Displays Current Song Queue"""
    string = "**" + str(len(song_queue)) +" Song(s) in Queue**\n"
    for player in song_queue:
        string += ':white_small_square: ``{}``\n'.format(player.title)
    await ctx.send(string)

@bot.command()
async def clear(ctx: commands.Context):
    """Clears the Song Queue"""
    if (len(song_queue) > 0):
        song_queue.clear()
        if (not ctx.voice_client == None and ctx.voice_client.is_playing()):
            ctx.voice_client.stop()
            await ctx.send('**Cleared Song Queue**')
    else:
        await ctx.send("Queue is already empty!")

@play.before_invoke
async def ensure_voice(ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.") 

@bot.command()
async def id(ctx, user: discord.User):
    """Says your Discord ID Number"""
    await ctx.send(f'{user.name}\'s ID is {user.id}')

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {member.joined_at}')


@bot.group()
async def cool(ctx):
    """Says if a user is cool.
    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')


bot.run(token)
