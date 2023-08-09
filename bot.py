import asyncio
import constants
import discord
import os
import re
from discord.ext import commands
from better_profanity import profanity

# Create bot instance and set command prefix
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
your_mom = []
swears = []

#Setup Function
@bot.event
async def setup_hook():
  for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        await bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"Loaded Cog: {filename[:-3]}")

def add_your_mom(guild_id):
  global your_mom
  count = 1
  found = False
  for line in your_mom:
    if int(line[0]) == guild_id:
      found = True
      count = int(line[1]) + 1
      line[1] = str(count)
      break
  if not found:
    your_mom.append([str(guild_id), str(count)])
  with open("files/your_mom.csv", mode="w") as file:
    for line in your_mom:
      file.write(line[0] + "," + line[1] + "\n")
  return count

def add_swears(guild_id):
  global swears
  count = 1
  found = False
  for line in swears:
    if int(line[0]) == guild_id:
      found = True
      count = int(line[1]) + 1
      line[1] = str(count)
      break
  if not found:
    swears.append([str(guild_id), str(count)])
  with open("files/swears.csv", mode="w") as file:
    for line in swears:
      file.write(line[0] + "," + line[1] + "\n")
  return count

# Bot event: on ready
@bot.event
async def on_ready():
  global your_mom
  global swears
  print(f'Bot connected as {bot.user}')
  with open("files/your_mom.csv", mode="r") as file:
    for line in file:
      items = line.split(",")
      your_mom.append(items)
  with open("files/swears.csv", mode="r") as file:
    for line in file:
      items = line.split(",")
      swears.append(items)

@bot.event
async def on_message(message: discord.Message):
  if message.author.id == constants.bot_id:
    return
  await bot.process_commands(message)
  m = re.search("(?:yo|your|ur|tu|ya)\s*(?:mama|mother|mum|mom|madre|mommy)", message.content, re.IGNORECASE)
  if not m == None:
    count = add_your_mom(message.guild.id)
    await message.channel.send(f"Your mom counter: {count}")
  if profanity.contains_profanity(message.content):
    count = add_swears(message.guild.id)
    await message.channel.send(f"Swear counter: {count}")

@bot.event
async def on_voice_state_update(member: discord.member.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
  if before.channel is None and after.channel is not None:
    if not discord.utils.get(bot.voice_clients, guild=member.guild) == None:
      return
    if member.id not in constants.intros:
      return
    voice_client = await after.channel.connect()
    voice_client.play(discord.FFmpegPCMAudio(constants.intros[member.id]))
    while voice_client.is_playing():
        await asyncio.sleep(1)
    await voice_client.disconnect()

# Sync Bot commands
@bot.hybrid_command()
async def sync(ctx: commands.Context):
  """Syncs Discord UI with bot slash commands"""
  
  if not ctx.author.id == constants.my_id:
    await ctx.send("You do not have access to this command.")
    return
  fmt = await bot.tree.sync()
  await ctx.send(f"Sync'd {len(fmt)} commands to the current server")

# Get bot token
def get_token():
  token = ""
  with open('files/devtoken.txt', mode='r') as file:
    token = file.read()
  return token

# Run the bot
bot.run(token=get_token())