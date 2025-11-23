from functools import wraps
from utils import owner_only_bot
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
# FIX: Add an optional argument to resolve the CommandSignatureMismatch for hybrid commands
async def sync(ctx: commands.Context, global_sync: bool = False): 
    """Syncs Discord UI with bot slash commands"""
    # Send immediate acknowledgement, then edit with results so slash-commands
    # (interactions) get an early response and the response is updated later.
    try:
        # Send initial message depending on invocation type
        sent_msg = None
        if getattr(ctx, "interaction", None):
            # Interaction (slash) invocation
            try:
                await ctx.interaction.response.send_message("Working on it...")
                # fetch the original response message object to edit later
                sent_msg = await ctx.interaction.original_response()
            except Exception:
                # fallback to regular send
                sent_msg = await ctx.send("Working on it...")
        else:
            sent_msg = await ctx.send("Working on it...")

        # If you want to use the argument for a global sync:
        if global_sync:
            fmt = await bot.tree.sync()
            result_text = f"Synced {len(fmt)} commands globally"
        else:
            # Sync only to the current guild (if applicable)
            fmt = await bot.tree.sync(guild=ctx.guild)
            result_text = f"Synced {len(fmt)} commands to the current server"

        logger.info(f"Synced {len(fmt)} commands by {getattr(ctx.author, 'name', 'unknown')}")

        # Edit the original acknowledgement message with the result
        try:
            await sent_msg.edit(content=result_text)
        except Exception:
            # If editing fails, just send a new message
            await ctx.send(result_text)
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        try:
            # You need `sent_msg` to be defined here, so ensure the initial send succeeds
            await sent_msg.edit(content=f"ERROR: Failed to sync commands")
        except Exception:
            # last-resort: log only
            logger.exception("Failed to notify about sync error")


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
