"""Utility for slash command quick response pattern.

Provides a helper to send an immediate acknowledgement for slash commands
and return the message so it can be edited with actual results later.
"""

from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


async def send_initial_response(ctx: commands.Context, initial_text: str = "Working on it..."):
	"""Send an immediate response for slash commands, or a regular message for prefix commands.

	Args:
		ctx: The command context (hybrid commands have access to both interaction and regular context).
		initial_text: The text to send as the initial acknowledgement (default: "Working on it...").

	Returns:
		The message object that was sent, which can be edited later with actual results.

	This handles:
	- Slash command (interaction) invocations: responds via interaction.response and fetches the original response.
	- Prefix command invocations: sends a regular message via ctx.send().
	- Fallbacks if the primary method fails.
	"""
	sent_msg = None

	if getattr(ctx, "interaction", None):
		# Interaction (slash) invocation
		try:
			await ctx.interaction.response.send_message(initial_text)
			# Fetch the original response message object to edit later
			sent_msg = await ctx.interaction.original_response()
			logger.debug(f"Sent initial slash response: '{initial_text}'")
		except Exception as e:
			logger.debug(f"Failed to send slash response, falling back to ctx.send: {e}")
			# Fallback to regular send
			sent_msg = await ctx.send(initial_text)
	else:
		# Prefix command invocation
		sent_msg = await ctx.send(initial_text)
		logger.debug(f"Sent initial prefix response: '{initial_text}'")

	return sent_msg


async def edit_response(sent_msg, new_content: str, fallback_ctx: commands.Context = None):
	"""Edit the initial response message with final results.

	Args:
		sent_msg: The message object returned from send_initial_response.
		new_content: The new content to display in the edited message.
		fallback_ctx: Optional context to fall back to if editing fails (will send a new message instead).

	Tries to edit the message in-place. If editing fails and fallback_ctx is provided,
	sends a new message instead.
	"""
	try:
		await sent_msg.edit(content=new_content)
		logger.debug(f"Edited response with new content")
	except Exception as e:
		logger.debug(f"Failed to edit response message: {e}")
		if fallback_ctx:
			try:
				await fallback_ctx.send(new_content)
				logger.debug(f"Sent fallback message instead")
			except Exception as e2:
				logger.error(f"Failed to send fallback message: {e2}")
