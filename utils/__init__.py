"""Utils package."""

import logging
from functools import wraps

from utils.constants import my_id
from discord.ext import commands

logger = logging.getLogger(__name__)


def owner_only_cog(func):
	"""Decorator to check if the command invoker's user ID matches my_id."""
	@wraps(func)
	async def wrapper(self, ctx: commands.Context, *args, **kwargs):
		if my_id is None:
			await ctx.send("Owner ID not configured.")
			logger.warning("Owner command called but my_id is None")
			return
		if ctx.author.id != my_id:
			await ctx.send("You do not have permission to use this command.")
			logger.warning(f"Unauthorized command attempt by {ctx.author.id} ({ctx.author.name})")
			return
		return await func(self, ctx, *args, **kwargs)
	return wrapper

def owner_only_bot(func):
    """Decorator to check if the command invoker's user ID matches my_id."""
    # FIX: Remove 'self' from the wrapper signature if the command is NOT inside a Cog.
    @wraps(func)
    async def wrapper(ctx: commands.Context, *args, **kwargs):
        if my_id is None:
            await ctx.send("Owner ID not configured.")
            logger.warning("Owner command called but my_id is None")
            return
        
        # Check against bot owner ID
        if ctx.author.id != my_id:
            await ctx.send("You do not have permission to use this command.")
            logger.warning(f"Unauthorized command attempt by {ctx.author.id} ({ctx.author.name})")
            return
            
        # FIX: Also ensure 'func' is called without 'self'
        return await func(ctx, *args, **kwargs) 
        
    return wrapper

