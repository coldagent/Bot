"""Cog: save server users to per-user CSV files.

Usage:
- Command: `!save_users` (or the bot prefix you use)
- Output path: `files/servers/<servername>/users/<username>.csv`

Notes:
- The bot requires the `members` intent enabled and permission to view server members and roles.
"""

import json
import os
import re
from pathlib import Path
from functools import wraps

import discord
from discord.ext import commands
import constants
import asyncio

def owner_only(func):
	"""Decorator to check if the command invoker's user ID matches my_id."""
	@wraps(func)
	async def wrapper(self, ctx: commands.Context, *args, **kwargs):
		if constants.my_id is None:
			await ctx.send("Owner ID not configured.")
			return
		if ctx.author.id != constants.my_id:
			await ctx.send("You do not have permission to use this command.")
			return
		return await func(self, ctx, *args, **kwargs)
	return wrapper

def _sanitize_name(name: str, max_length: int = 200) -> str:
	"""Sanitize a string to be a safe filename on most filesystems.

	Replaces characters that are invalid on Windows/Unix with underscores
	and trims length.
	"""
	# Remove control characters
	name = re.sub(r"[\x00-\x1f\x7f]", "", name)
	# Replace invalid path characters
	invalid = '<>:"/\\|?*'
	replace_table = {ord(c): "_" for c in invalid}
	safe = name.translate(replace_table)
	# Also replace any remaining path separators and strip
	safe = safe.replace(os.path.sep, "_").strip()
	if not safe:
		safe = "unknown"
	return safe[:max_length]

class ServerSaver(commands.Cog):
	"""Cog providing a command to save all guild members to files."""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.hybrid_command()
	@owner_only
	async def save_users(self, ctx: commands.Context):
		"""Save each member of the guild"""
		guild = ctx.guild
		if guild is None:
			await ctx.send("This command must be used in a guild.")
			return

		# Directory path
		base = Path("files") / "servers" / _sanitize_name(guild.name) / "users"
		base.mkdir(parents=True, exist_ok=True)

		saved = 0
		errors = 0
		for member in guild.members:
			try:
				username = _sanitize_name(member.name)
				# Write to the sanitized username file (overwrite if it exists)
				filename = base / f"{username}.csv"

				# collect roles (exclude @everyone / default role)
				roles = [r.name for r in member.roles if r != guild.default_role]
				roles_line = ",".join(roles)

				with filename.open("w", encoding="utf-8", newline="\n") as fh:
					fh.write(str(member.id) + "\n")
					fh.write(roles_line + "\n")

				saved += 1
			except Exception:
				errors += 1

		# Save roles for the guild
		roles_dir = Path("files") / "servers" / _sanitize_name(guild.name) / "roles"
		roles_dir.mkdir(parents=True, exist_ok=True)

		roles_saved = 0
		roles_errors = 0
		for role in guild.roles:
			try:
				rname = _sanitize_name(role.name)
				rfile = roles_dir / f"{rname}.csv"
				# Try to get a list of permission names that are enabled on the role
				perms_line = ""
				try:
					if hasattr(role.permissions, "to_dict"):
						perms = role.permissions.to_dict()
						perms_line = ",".join([k for k, v in perms.items() if v])
					else:
						perms_line = str(getattr(role.permissions, "value", role.permissions))
				except Exception:
					perms_line = str(getattr(role.permissions, "value", role.permissions))

				with rfile.open("w", encoding="utf-8", newline="\n") as rf:
					# Line 1: role name
					rf.write(role.name + "\n")
					# Line 2: role color in hex (e.g. #a1b2c3)
					try:
						color_hex = f"#{role.color.value:06x}"
					except Exception:
						color_hex = "#000000"
					rf.write(color_hex + "\n")
					# Line 3: comma-separated enabled permission names
					rf.write(perms_line + "\n")

				roles_saved += 1
			except Exception:
				roles_errors += 1

		await ctx.send(f"Saved {saved} members to `{base}` (Errors: {errors}). Saved {roles_saved} roles to `{roles_dir}` (Errors: {roles_errors}).")

	@commands.hybrid_command()
	@owner_only
	async def recreate_roles(self, ctx: commands.Context, source_server: str):
		"""Recreate roles in this guild from saved roles for `source_server`.

		Reads files from `files/servers/<source_server>/roles/*.csv` where each file
		contains:
		- Line 1: role name
		- Line 2: color hex (e.g. #a1b2c3)
		- Line 3: permission dict in JSON format (e.g. {"permission_name": true/false, ...})

		If a role with the same name already exists in the destination guild, it will
		be updated (color & permissions). Otherwise the role will be created.
		"""
		guild = ctx.guild
		if guild is None:
			await ctx.send("This command must be used inside a guild.")
			return

		src_dir = Path("files") / "servers" / _sanitize_name(source_server) / "roles"
		if not src_dir.exists():
			await ctx.send(f"No saved roles found for server `{source_server}` at `{src_dir}`.")
			return

		created = 0
		updated = 0
		errors = 0
		for rf in src_dir.glob("*.csv"):
			try:
				with rf.open("r", encoding="utf-8") as fh:
					lines = [l.rstrip("\n") for l in fh.readlines()]
					if not lines:
						continue
					role_name = lines[0]
					color_hex = lines[1] if len(lines) > 1 else "#000000"
					perms_line = lines[2] if len(lines) > 2 else ""

					# parse color
					try:
						color_val = int(color_hex.lstrip("#"), 16)
					except Exception:
						color_val = 0
					colour = discord.Colour(color_val)

				# build permissions from dict format or integer value
				perms = discord.Permissions.none()
				if perms_line:
					try:
						# Try to parse as JSON dict first
						perms_dict = json.loads(perms_line)
						for pname, enabled in perms_dict.items():
							if enabled and hasattr(perms, pname):
								setattr(perms, pname, True)
					except Exception:
						# If not JSON, try to parse as integer permission value
						try:
							perm_int = int(perms_line)
							perms = discord.Permissions(perm_int)
						except (ValueError, TypeError):
							# If all else fails, use no permissions
							pass					# skip everyone role
					if role_name == guild.default_role.name:
						# we cannot create the @everyone role; skip it
						continue

				# find existing role by exact name
				existing = discord.utils.get(guild.roles, name=role_name)
				if existing:
					# Update permissions and color for existing role
					#await existing.edit(permissions=perms, colour=colour)
					updated += 1
				else:
					await guild.create_role(name=role_name, permissions=perms, colour=colour)
					created += 1

			except Exception as e:
				print(f"Error recreating role `{role_name}`: {e}")
				errors += 1

		await ctx.send(f"Roles recreated: created={created}, updated={updated}, errors={errors}.")

		# Now assign roles to users based on saved role assignments
		users_dir = Path("files") / "servers" / _sanitize_name(source_server) / "users"
		if not users_dir.exists():
			await ctx.send("No saved users found to reassign roles.")
			return

		users_updated = 0
		users_errors = 0
		for uf in users_dir.glob("*.csv"):
			try:
				with uf.open("r", encoding="utf-8") as fh:
					lines = [l.rstrip("\n") for l in fh.readlines()]
					if not lines:
						continue
					user_id = int(lines[0])
					saved_roles_line = lines[1] if len(lines) > 1 else ""

					# Find the member in the current guild by ID
					member = guild.get_member(user_id)
					if not member:
						users_errors += 1
						continue

					# Parse saved role names
					saved_role_names = [r.strip() for r in (saved_roles_line.split(",") if saved_roles_line else []) if r.strip()]

					# Find corresponding role objects in current guild
					roles_to_assign = []
					for role_name in saved_role_names:
						role = discord.utils.get(guild.roles, name=role_name)
						if role:
							roles_to_assign.append(role)

					# Assign all roles to the member
					if roles_to_assign:
						await member.add_roles(*roles_to_assign)

					users_updated += 1

			except Exception:
				users_errors += 1

		await ctx.send(f"Roles reassigned to users: updated={users_updated}, errors={users_errors}.")

	@commands.hybrid_command()
	@owner_only
	async def delete_all_messages(self, ctx: commands.Context):
		"""Delete all channels in the server.

		This command will delete every channel in the guild. Use with caution!
		"""
		guild = ctx.guild
		if guild is None:
			await ctx.send("This command must be used inside a guild.")
			return

		await ctx.send("Starting deletion of all channels in the server...")

		deleted = 0
		errors = 0
		for channel in list(guild.channels):
			try:
				await channel.delete()
				deleted += 1
			except Exception:
				errors += 1

		

		# Recreate a default `general` channel and send the summary there
		try:
			new_channel = await guild.create_text_channel("general")
			await new_channel.send(f"Finished! Total channels deleted: {deleted}, errors: {errors}.")
			await new_channel.send("Created channel: #general")
		except Exception as e:
			# Log in console if we cannot create the channel
			print(f"Finished! Total channels deleted: {deleted}, errors: {errors}.")
			print(f"Could not create #general: {e}")

	@commands.hybrid_command()
	@owner_only
	async def kick_all(self, ctx: commands.Context):
		"""Kick all members from the server except the owner (constants.my_id).

		Use with caution! This will kick everyone except the ID listed in constants.my_id.
		"""
		guild = ctx.guild
		if guild is None:
			await ctx.send("This command must be used inside a guild.")
			return

		await ctx.send("Starting to kick all members except the owner...")

		kicked = 0
		skipped = 0
		errors = 0
		for member in guild.members:
			# Skip the owner
			if member.id == constants.my_id:
				skipped += 1
				continue
			# Skip the bot itself
			if member.id == self.bot.user.id:
				skipped += 1
				continue

			try:
				await member.kick(reason="Kicked by kick_all command")
				kicked += 1
			except Exception as e:
				print(f"Error kicking member {member.id}: {e}")
				errors += 1

		await ctx.send(f"Kick complete: kicked={kicked}, skipped={skipped}, errors={errors}.")

	@commands.hybrid_command(name="invite_saved_users")
	@owner_only
	async def invite_saved_users(self, ctx: commands.Context, source_server: str):
		"""Invite all users saved for `source_server` to the current guild.

		Reads `files/servers/<source_server>/users/*.csv` and DMs each user
		an invite link to the current guild. Matches users by saved user ID.
		"""
		guild = ctx.guild
		if guild is None:
			await ctx.send("This command must be used inside a guild.")
			return

		users_dir = Path("files") / "servers" / _sanitize_name(source_server) / "users"
		if not users_dir.exists():
			await ctx.send(f"No saved users found for server `{source_server}` at `{users_dir}`.")
			return

		# Find a text channel where we can create an invite
		invite_channel = None
		for ch in guild.text_channels:
			if ch.permissions_for(guild.me).create_instant_invite:
				invite_channel = ch
				break
		if invite_channel is None:
			await ctx.send("I don't have permission to create invites in any text channel.")
			return

		# Create a permanent invite
		try:
			invite = await invite_channel.create_invite(max_uses=0, max_age=0, unique=False)
		except Exception as e:
			await ctx.send(f"Failed to create invite: {e}")
			return

		sent = 0
		failed = 0
		for uf in users_dir.glob("*.csv"):
			try:
				with uf.open("r", encoding="utf-8") as fh:
					lines = [l.rstrip("\n") for l in fh.readlines()]
					if not lines:
						continue
					user_id = int(lines[0])
				# Fetch user object even if they're not in the bot's cache
				try:
					user = await self.bot.fetch_user(user_id)
				except Exception:
					failed += 1
					continue

				# DM the invite
				try:
					await user.send(f"This is coldagent's bot. Our former server owner, Demanchus' account was hacked and The Chocobros server was deleted. You were a member of that server, so you are invited to the new server we are using to replace it.\nYou've been invited to join **{guild.name}**: {invite.url}")
					sent += 1
				except Exception:
					failed += 1
				# small delay to avoid hitting strict rate limits
				await asyncio.sleep(0.5)
			except Exception:
				failed += 1

		await ctx.send(f"Invite DM complete: sent={sent}, failed={failed}.")


async def setup(bot: commands.Bot):
	await bot.add_cog(ServerSaver(bot))
