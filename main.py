import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 📦 Lijst van alle extensies (cogs map)
EXTENSIONS = [
    "cogs.invite_post",
    "cogs.invite_manager",
    "cogs.verificatehandler",
    "cogs.timeout_blacklist",
    "cogs.vouch_commands",
    "cogs.player_notes",
    "cogs.voucher_reputation"
]

@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slashcommands gesynchroniseerd")
    except Exception as e:
        print(f"❌ Slashcommand sync fout: {e}")

async def main():
    # Haal de bot-token uit de secret file
    with open('/etc/secrets/BOT_TOKEN', 'r') as f:
        token = f.read().strip()

    # Laad alle extensies
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Extension geladen: {ext}")
        except Exception as e:
            print(f"❌ Fout bij laden van {ext}: {e}")

    # Start de bot met de token
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
