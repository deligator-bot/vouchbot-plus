import os
from keep_alive import keep_alive
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ VouchBot+ is online as {bot.user}")

keep_alive()
bot.run(os.getenv("BOT_TOKEN"))