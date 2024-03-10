import discord
import re
import constants
from better_profanity import profanity
from discord.ext import commands

class Counter(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.your_mom = []
    self.swears = []
    self.load_counters()
    profanity.load_censor_words_from_file("./files/bad_words.txt")
    
  def load_counters(self):
    with open("./files/your_mom.csv", mode="r") as file:
        for line in file:
            items = line.split(",")
            self.your_mom.append(items)
    with open("./files/swears.csv", mode="r") as file:
        for line in file:
            items = line.split(",")
            self.swears.append(items)

  def add_your_mom(self, guild_id):
    found = False
    for line in self.your_mom:
      if len(line) == 2 and int(line[0]) == guild_id:
        found = True
        count = int(line[1]) + 1
        line[1] = str(count)
        break
    if not found:
      self.your_mom.append([str(guild_id), "1"])
    with open("./files/your_mom.csv", mode="w") as file:
      for line in self.your_mom:
        if not len(line) == 2:
          continue
        file.write(line[0] + "," + line[1] + "\n")

  def get_your_mom_count(self, guild_id):
    for line in self.your_mom:
      if len(line) == 2 and int(line[0]) == guild_id:
        return int(line[1])
    return 0

  def add_swears(self, guild_id):
    found = False
    for line in self.swears:
      if len(line) == 2 and int(line[0]) == guild_id:
        found = True
        count = int(line[1]) + 1
        line[1] = str(count)
        break
    if not found:
      self.swears.append([str(guild_id), "1"])
    with open("./files/swears.csv", mode="w") as file:
      for line in self.swears:
        if not len(line) == 2:
          continue
        file.write(line[0] + "," + line[1] + "\n")

  def get_swear_count(self, guild_id):
    for line in self.swears:
      if len(line) == 2 and int(line[0]) == guild_id:
        return int(line[1])
    return 0

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.author.id == constants.bot_id:
      return
    mom_words = re.search("(?:yo|your|ur|tu|ya)\s*(?:mama|mother|mum|mom|madre|mommy)", message.content, re.IGNORECASE)
    if not mom_words == None:
      self.add_your_mom(message.guild.id)
    if profanity.contains_profanity(message.content):
      self.add_swears(message.guild.id)
  
  # Bot command: counter
  @commands.hybrid_command()
  async def counter(self, ctx: commands.Context, arg=""):
    arg = str.lower(arg)
    if arg == "mom":
      await ctx.send(f"Your Mom Count: {self.get_your_mom_count(ctx.guild.id)}")
    elif arg == "swear":
      await ctx.send(f"Swear Count: {self.get_swear_count(ctx.guild.id)}")
    else:
      await ctx.send("Please specify one of the following counters as a command arg: \n[mom, swear]")

async def setup(bot):
  await bot.add_cog(Counter(bot))
