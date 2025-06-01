import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Nodig voor member join events

bot = commands.Bot(command_prefix="/", intents=intents)

# Webserver voor Render keep-alive
app = Flask('')

@app.route('/')
def home():
    return "VouchBot+ is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# Log-in bevestiging
@bot.event
async def on_ready():
    print(f'{bot.user} is online.')

# Testcommando
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# ✅ Hier komt alle logica voor:
# - vouch invite links
# - verificatiekanaal pings
# - vouchreacties (positief/negatief)
# - rollen toekennen
# - BM-run kanaal beheer
# - voicekanaal aanmaken bij /startbmrun
# - /checkvouch en /strikevoucher
# (Deze logica is hieronder nog niet toegevoegd – volgt in aparte modules of functies.)

# Launch bot
keep_alive()
with open('/etc/secrets/BOT_TOKEN', 'r') as f:
    token = f.read().strip()

bot.run(token)
