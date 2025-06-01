import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import json

# === Keep-alive server ===
app = Flask('')

@app.route('/')
def home():
    return "VouchBot+ is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# === Discord bot setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# === Simpele lokale JSON-database ===
DB_FILE = 'db.json'

def load_data():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"vouches": {}, "strikes": {}}

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# === Event: bot is online ===
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online.")

# === Commando: /ping ===
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# === Commando: /checkvouch @user ===
@bot.command()
async def checkvouch(ctx, member: discord.Member):
    data = load_data()
    vouches = data.get("vouches", {})
    strikes = data.get("strikes", {})

    voucher = vouches.get(str(member.id))
    missers = strikes.get(voucher, 0) if voucher else 0

    if voucher:
        await ctx.send(
            f"The player {member.mention} has been vouched by <@{voucher}>.\n"
            f"🛑 The voucher has made `{missers}` mistake(s)."
        )
    else:
        await ctx.send(f"{member.mention} has no vouch record.")

# === Commando: /strikevoucher @user ===
@bot.command()
@commands.has_permissions(administrator=True)
async def strikevoucher(ctx, voucher: discord.Member):
    data = load_data()
    strikes = data.get("strikes", {})

    strikes[str(voucher.id)] = strikes.get(str(voucher.id), 0) + 1
    data["strikes"] = strikes
    save_data(data)

    await ctx.send(f"⚠️ Strike added for {voucher.mention}. Total: `{strikes[str(voucher.id)]}`.")

# === Launch bot ===
keep_alive()
with open('/etc/secrets/BOT_TOKEN', 'r') as f:
    token = f.read().strip()

bot.run(token)
