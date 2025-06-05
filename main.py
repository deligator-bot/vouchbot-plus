import discord
from discord.ext import commands
import asyncio
import os

# ✅ Intents instellen
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.reactions = True

# ✅ Bot aanmaken
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Keep alive server (Replit / Render)
from keep_alive import keep_alive
keep_alive()

# Sync slash commands on_ready event
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# ✅ Cogs automatisch laden
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            await bot.load_extension(f"cogs.{cog_name}")

# ✅ Main starten
async def main():
    await load_extensions()
    token = None
    try:
        with open('/etc/secrets/BOT_TOKEN', 'r') as f:
            token = f.read().strip()
    except:
        print("⚠️ Kan token niet inlezen!")
    if token:
        await bot.start(token)
    else:
        print("❌ Geen geldige token gevonden.")

# ✅ Bot starten
asyncio.run(main())
