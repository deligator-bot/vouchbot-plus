import discord
from discord.ext import commands
import asyncio
import os

# 📦 Configureer de intents (alles aan, inclusief Presence en Members)
intents = discord.Intents.all()

# 📦 Bot setup met command prefix (slashcommands gebruiken app_commands)
bot = commands.Bot(command_prefix="!", intents=intents)

# 📦 Lijst met extensies (cogs)
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
    # ✅ Laad alle extensies (cogs)
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Extension geladen: {ext}")
        except Exception as e:
            print(f"❌ Fout bij laden van {ext}: {e}")

    # ✅ Lees de token uit bestand (Render -> /etc/secrets/BOT_TOKEN)
    try:
        with open('/etc/secrets/BOT_TOKEN', 'r') as f:
            bot_token = f.read().strip()
            print("🔐 BOT_TOKEN succesvol opgehaald uit /etc/secrets/")
    except Exception as e:
        print(f"❌ Fout bij ophalen van BOT_TOKEN: {e}")
        return

    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(main())
