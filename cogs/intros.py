import asyncio
import discord
import constants
from discord.ext import commands

class Intros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.toggle = {}
        self.load_toggle()

    def load_toggle(self):
        with open("./files/intro_toggle.csv", mode="r") as file:
            for line in file:
                items = line.split(",")
                self.toggle[int(items[0])] = bool(items[1])
        missing = False
        for id in constants.intros:
            if id not in self.toggle:
                self.toggle[id] = True
                missing = True
        if missing:
            self.rewrite_intro()
            
    def rewrite_intro(self):
        with open("./files/intro_toggle.csv", mode="w") as file:
            for key in self.toggle:
                file.write(str(key) + "," + str(self.toggle.get(key)) + "\n")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.member.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
        if before.channel is None and after.channel is not None:
            if not discord.utils.get(self.bot.voice_clients, guild=member.guild) == None or member.id not in constants.intros or not self.toggle.get(member.id):
                return
            voice_client = await after.channel.connect()
            voice_client.play(discord.FFmpegPCMAudio(constants.intros[member.id]))
            while voice_client.is_playing():
                await asyncio.sleep(1)
            await voice_client.disconnect()
    
    @commands.hybrid_command()
    async def toggle_intro(self, ctx: commands.Context):
        """Toggles your intro on or off (default is on)"""
        id = ctx.author.id
        if id not in constants.intros:
            await ctx.send("You do not have an intro. Ask Zach to set your intro up.")
            return
        self.toggle[id] = not self.toggle.get(id)
        self.rewrite_intro()
        await ctx.send(f"Intro for {ctx.author.mention}: {'ON' if self.toggle.get(id) else 'OFF'}")

async def setup(bot):
    await bot.add_cog(Intros(bot))
