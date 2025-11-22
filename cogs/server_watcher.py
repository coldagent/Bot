"""Cog: monitor channel per-guild and send automatic messages.

Commands:
- `monitor_channel` (hybrid): register the current channel as the monitor channel for the guild.

Behavior:
- Saves the selected channel id to `files/servers/monitors/<servername>/channel.txt`.
- When a user logs into Discord from the web client, if a monitor channel is configured, send a message there.

Notes:
- Requires `presences` intent to receive `on_presence_update` events.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
from utils.logging_setup import setup_logging

# Ensure logging is configured (idempotent)
setup_logging()

logger = logging.getLogger(__name__)


def _sanitize_name(name: str, max_length: int = 200) -> str:
    """Sanitize a string to be a safe filename on most filesystems."""
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    invalid = '<>:"/\\|?*'
    replace_table = {ord(c): "_" for c in invalid}
    safe = name.translate(replace_table)
    safe = safe.replace(os.path.sep, "_").strip()
    if not safe:
        safe = "unknown"
    return safe[:max_length]


class ServerWatcher(commands.Cog):
    """Watch servers and send automatic messages to configured channel."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="monitor_channel", description="Set the current channel as the monitor channel for this guild.")
    @commands.guild_only()
    async def monitor_channel(self, ctx: commands.Context):
        """Register the current channel as the monitor channel for this guild.

        The channel id is saved to `files/servers/monitors/<servername>/channel.txt`.
        """
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command must be run in a guild channel.")
            logger.warning("monitor_channel called outside of a guild")
            return

        try:
            base = Path("files") / "servers" / _sanitize_name(guild.name) / "monitors"
            base.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create monitor directory for {guild.name}: {e}")
            await ctx.send(f"An error occured.")
            return

        channel_file = base / "channel.txt"
        try:
            with channel_file.open("w", encoding="utf-8") as fh:
                fh.write(str(ctx.channel.id) + "\n")
            logger.info(f"Monitor channel set to {ctx.channel.id} for guild {guild.name}")
            await ctx.send(f"Monitor channel set to {ctx.channel.mention} for guild '{guild.name}'.")
        except Exception as e:
            logger.error(f"Failed to write monitor configuration for {guild.name} (channel {ctx.channel.id}): {e}")
            await ctx.send(f"Could not write monitor configuration: {e}")

    def _get_monitor_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Return the configured monitor channel for `guild`, or None."""
        base = Path("files") / "servers" / _sanitize_name(guild.name) / "monitors"
        channel_file = base / "channel.txt"
        if not channel_file.exists():
            logger.debug(f"No monitor configuration found for {guild.name}")
            return None
        try:
            cid = int(channel_file.read_text(encoding="utf-8").strip())
            channel = guild.get_channel(cid) or self.bot.get_channel(cid)
            if channel is None:
                logger.warning(f"Monitor channel {cid} not found for {guild.name}")
            return channel
        except Exception as e:
            logger.error(f"Failed to read monitor channel for {guild.name}: {e}")
            return None

    @commands.Cog.listener(name="on_presence_update")
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Send a message when a user logs in via web client."""
        try:
            # Check if the user's client status changed to web
            if before.client_status == after.client_status:
                return

            # Check if web is now active (was not before)
            web_before = before.client_status.web if before.client_status else None
            web_after = after.client_status.web if after.client_status else None

            if web_before is None and web_after is not None:
                # User just logged into web client
                guild = after.guild
                logger.debug(f"User {after.name} [id: {after.id}] logged in from web in {guild.name}")
                chan = self._get_monitor_channel(guild)
                if chan is None:
                    logger.debug(f"No monitor channel configured for {guild.name}")
                    return
                try:
                    await chan.send(f"User {after.name} [id: {after.id}] logged in from web.")
                    logger.info(f"Sent web login notification for {after.name} ({after.id}) to {guild.name}")
                except Exception as e:
                    logger.error(f"Failed to send web login notification for {after.id} in {guild.name}: {e}")
        except Exception as e:
            logger.error(f"Error in on_presence_update for {after.id}: {e}")
async def setup(bot: commands.Bot):
    await bot.add_cog(ServerWatcher(bot))
