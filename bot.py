from functools import wraps
from utils import owner_only_bot
from utils.slash_response import send_initial_response, edit_response
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
@owner_only_bot
async def sync(ctx: commands.Context, global_sync: bool = False):
    """Syncs Discord UI with bot slash commands"""
    try:
        # Send initial "Working on it..." response
        sent_msg = await send_initial_response(ctx)

        # Sync commands (global or guild-specific)
        if global_sync:
            fmt = await bot.tree.sync()
            result_text = f"Synced {len(fmt)} commands globally"
        else:
            fmt = await bot.tree.sync(guild=ctx.guild)
            result_text = f"Synced {len(fmt)} commands to the current server"

        logger.info(f"Synced {len(fmt)} commands by {getattr(ctx.author, 'name', 'unknown')}")

        # Edit with final results
        await edit_response(sent_msg, result_text, fallback_ctx=ctx)
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        await ctx.send(f"ERROR: Failed to sync commands: {e}")


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
