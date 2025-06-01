import asyncio

async def load_extensions():
    await bot.load_extension("invite_manager")
    await bot.load_extension("verification_handler")
    await bot.load_extension("vouch_commands")

# Start de Flask-server + bot
keep_alive()

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

asyncio.run(main())
