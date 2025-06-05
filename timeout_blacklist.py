import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta

# Log channel IDs
TIMEOUT_LOG_CHANNEL_ID = 1380179996114554950
BLACKLIST_LOG_CHANNEL_ID = 1380179997515317279

# Timeout settings
TIMEOUT_DURATION_DAYS = 7
TIMEOUT_WINDOW_DAYS = 30  # Window to count timeouts
MAX_TIMEOUTS_BEFORE_BLACKLIST = 2

class TimeoutBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_history = {}  # user_id -> list of datetime objects
        self.active_timeouts = {}  # user_id -> expiry datetime
        self.blacklist = set()
        self.cleanup_loop.start()

    async def log_to_channel(self, guild, channel_id, message):
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

    def add_timeout(self, user_id):
        now = datetime.utcnow()
        expiry = now + timedelta(days=TIMEOUT_DURATION_DAYS)

        if user_id not in self.timeout_history:
            self.timeout_history[user_id] = []
        self.timeout_history[user_id].append(now)
        self.active_timeouts[user_id] = expiry

    def count_recent_timeouts(self, user_id):
        now = datetime.utcnow()
        if user_id not in self.timeout_history:
            return 0
        recent = [t for t in self.timeout_history[user_id] if now - t <= timedelta(days=TIMEOUT_WINDOW_DAYS)]
        return len(recent)

    def has_active_timeout(self, user_id):
        expiry = self.active_timeouts.get(user_id)
        if expiry and datetime.utcnow() < expiry:
            return True
        return False

    def is_blacklisted(self, user_id):
        return user_id in self.blacklist

    @tasks.loop(minutes=10)
    async def cleanup_loop(self):
        now = datetime.utcnow()

        # Cleanup expired timeouts
        expired = [uid for uid, expiry in self.active_timeouts.items() if now >= expiry]
        for uid in expired:
            del self.active_timeouts[uid]

        # Cleanup old timeout history
        for user_id, times in list(self.timeout_history.items()):
            self.timeout_history[user_id] = [t for t in times if now - t <= timedelta(days=TIMEOUT_WINDOW_DAYS)]
            if not self.timeout_history[user_id]:
                del self.timeout_history[user_id]

    @app_commands.command(name="blacklist", description="Voegt een lid toe aan de blacklist.")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist(self, interaction: discord.Interaction, member: discord.Member):
        self.blacklist.add(member.id)
        await interaction.response.send_message(f"✅ {member.mention} is toegevoegd aan de blacklist.", ephemeral=False)
        await self.log_to_channel(interaction.guild, BLACKLIST_LOG_CHANNEL_ID, f"🚫 {member.mention} handmatig op de blacklist gezet door {interaction.user.mention}.")

    @app_commands.command(name="unblacklist", description="Verwijdert een lid van de blacklist.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unblacklist(self, interaction: discord.Interaction, member: discord.Member):
        if member.id in self.blacklist:
            self.blacklist.remove(member.id)
            await interaction.response.send_message(f"✅ {member.mention} is verwijderd van de blacklist.", ephemeral=False)
            await self.log_to_channel(interaction.guild, BLACKLIST_LOG_CHANNEL_ID, f"✅ {member.mention} verwijderd van de blacklist door {interaction.user.mention}.")
        else:
            await interaction.response.send_message(f"❌ {member.mention} staat niet op de blacklist.", ephemeral=True)

    async def apply_timeout(self, member: discord.Member):
        """Toe te passen bij join zonder bevestiging binnen 10 minuten."""
        guild = member.guild
        self.add_timeout(member.id)
        count = self.count_recent_timeouts(member.id)

        if count >= MAX_TIMEOUTS_BEFORE_BLACKLIST:
            self.blacklist.add(member.id)
            await self.log_to_channel(guild, BLACKLIST_LOG_CHANNEL_ID, f"🚫 {member.mention} automatisch geblacklist na {count} timeouts.")
            try:
                await member.send("🚫 Je bent geblacklist omdat je meerdere keren zonder bevestiging bent gejoined.")
            except discord.Forbidden:
                pass
            await member.kick(reason="Blacklist na meerdere timeouts")
        else:
            await self.log_to_channel(guild, TIMEOUT_LOG_CHANNEL_ID, f"⏰ {member.mention} heeft een timeout gekregen ({count}/{MAX_TIMEOUTS_BEFORE_BLACKLIST}).")
            try:
                await member.send(f"⏰ Je hebt een timeout gekregen van {TIMEOUT_DURATION_DAYS} dagen. Je mag daarna opnieuw proberen te joinen.")
            except discord.Forbidden:
                pass
            await member.kick(reason="Timeout: no vouch received")

async def setup(bot):
    await bot.add_cog(TimeoutBlacklist(bot))
