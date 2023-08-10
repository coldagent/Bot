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
    count = 1
    found = False
    for line in self.your_mom:
      if int(line[0]) == guild_id:
        found = True
        count = int(line[1]) + 1
        line[1] = str(count)
        break
    if not found:
      self.your_mom.append([str(guild_id), str(count)])
    with open("./files/your_mom.csv", mode="w") as file:
      for line in self.your_mom:
        file.write(line[0] + "," + line[1] + "\n")
    return count

  def add_swears(self, guild_id):
    count = 1
    found = False
    for line in self.swears:
      if int(line[0]) == guild_id:
        found = True
        count = int(line[1]) + 1
        line[1] = str(count)
        break
    if not found:
      self.swears.append([str(guild_id), str(count)])
    with open("./files/swears.csv", mode="w") as file:
      for line in self.swears:
        file.write(line[0] + "," + line[1] + "\n")
    return count

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.author.id == constants.bot_id:
      return
    m = re.search("(?:yo|your|ur|tu|ya)\s*(?:mama|mother|mum|mom|madre|mommy)", message.content, re.IGNORECASE)
    if not m == None:
      count = self.add_your_mom(message.guild.id)
      await message.channel.send(f"Your mom counter: {count}")
    profanity.load_censor_words_from_file("./files/bad_words.txt")
    if profanity.contains_profanity(message.content):
      count = self.add_swears(message.guild.id)
      await message.channel.send(f"Swear counter: {count}")

async def setup(bot):
  await bot.add_cog(Counter(bot))
