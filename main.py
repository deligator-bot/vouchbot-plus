import discord
from discord.ext import commands
import asyncio
import os

# ✅ Zorg dat je de BOT_TOKEN instelt als secret environment variable op Render

# 📦 Configureer de intents (alle aan, inclusief Presence en Members)
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

    # ✅ Haal de bot token uit de secret environment variabele (Render)
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("❌ BOT_TOKEN is niet ingesteld als environment variabele!")

    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(main())
