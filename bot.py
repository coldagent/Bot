import constants
import discord
import os
from discord.ext import commands

# Create bot instance and set command prefix

bot = commands.Bot(command_prefix='`', intents=discord.Intents.all())

#Setup Function
@bot.event
async def setup_hook():
  # Load Cogs
  for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        await bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"Loaded Cog: {filename[:-3]}")

# Bot event: on ready
@bot.event
async def on_ready():
  print(f'Bot connected as {bot.user}')

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
  with open('./files/token.txt', mode='r') as file:
    token = file.read()
  return token

# Run the bot
bot.run(token=get_token())
