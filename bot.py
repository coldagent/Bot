from functools import wraps
from utils import owner_only
import discord
import os
import logging
from discord.ext import commands
from utils.logging_setup import setup_logging


setup_logging()

logger = logging.getLogger("bot")

# Create bot instance and set command prefix
bot = commands.Bot(command_prefix="`", intents=discord.Intents.all())


# Setup Function
@bot.event
async def setup_hook():
  # Load Cogs
  try:
    cog_names = ""
    for filename in os.listdir("./cogs"):
      if filename.endswith(".py"):
        try:
          await bot.load_extension(f"cogs.{filename[:-3]}")
          cog_names += f"{filename[:-3]}, "
          
        except Exception as e:
          logger.error(f"Failed to load cog {filename[:-3]}: {e}")
    logger.info(f"Loaded Cogs: {cog_names[:-2]}")
  except Exception as e:
    logger.error(f"Error loading cogs: {e}")


# Bot event: on ready
@bot.event
async def on_ready():
  logger.info(f"Bot connected as {bot.user}")


# Sync Bot commands
@bot.hybrid_command(name="sync", description="Syncs Discord UI with bot slash commands")
@owner_only
async def sync(ctx: commands.Context):
  """Syncs Discord UI with bot slash commands"""

  try:
    fmt = await bot.tree.sync()
    logger.info(f"Synced {len(fmt)} commands by {ctx.author.name}")
    await ctx.send(f"Sync'd {len(fmt)} commands to the current server")
  except Exception as e:
    logger.error(f"Failed to sync commands: {e}")
    await ctx.send(f"Failed to sync commands: {e}")


# Get bot token
def get_token():
  token = ""
  try:
    with open("./files/token.txt", mode="r") as file:
      token = file.read().strip()
    logger.info("Bot token loaded successfully")
    return token
  except FileNotFoundError:
    logger.error("Token file not found at ./files/token.txt")
    raise
  except Exception as e:
    logger.error(f"Failed to load bot token: {e}")
    raise


# Run the bot
try:
  bot.run(token=get_token())
except Exception as e:
  logger.critical(f"Failed to run bot: {e}")
  raise
