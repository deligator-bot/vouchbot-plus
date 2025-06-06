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

# ✅ Keep alive server (Render / Replit)
from keep_alive import keep_alive
keep_alive()

# ✅ Slash commands syncen
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands gesynchroniseerd ({len(synced)} commands)")
    except Exception as e:
        print(f"❌ Slash commands sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# ✅ Cogs automatisch laden (alleen .py bestanden met setup)
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("keep") and filename != "__init__.py":
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                print(f"✅ Loaded: {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")

# ✅ Main functie
async def main():
    await load_extensions()
    
    # 🔐 Haal token op uit bestand
    token = None
    try:
        with open('/etc/secrets/BOT_TOKEN', 'r') as f:
            token = f.read().strip()
            print("🔐 Token succesvol ingelezen uit bestand.")
    except Exception as e:
        print(f"❌ Kon token niet inlezen: {e}")

    if token:
        await bot.start(token)
    else:
        print("❌ Geen geldige token gevonden.")

# ✅ Bot starten
asyncio.run(main())
