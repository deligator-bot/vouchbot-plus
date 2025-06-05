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
        self.blacklist = set()
        self.cleanup_loop.start()

    async def log_to_channel(self, guild, channel_id, message):
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

    def add_timeout(self, user_id):
        now = datetime.utcnow()
        if user_id not in self.timeout_history:
            self.timeout_history[user_id] = []
        self.timeout_history[user_id].append(now)

    def count_recent_timeouts(self, user_id):
        now = datetime.utcnow()
        if user_id not in self.timeout_history:
            return 0
        recent = [t for t in self.timeout_history[user_id] if now - t <= timedelta(days=TIMEOUT_WINDOW_DAYS)]
        return len(recent)

    @tasks.loop(minutes=10)
    async def cleanup_loop(self):
        now = datetime.utcnow()
        for user_id, times in list(self.timeout_history.items()):
            self.timeout_history[user_id] = [t for t in times if now - t <= timedelta(days=TIMEOUT_WINDOW_DAYS)]
            if not self.timeout_history[user_id]:
                del self.timeout_history[user_id]

    @app_commands.command(name="blacklist", description="Add a member to the blacklist.")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist(self, interaction: discord.Interaction, member: discord.Member):
        self.blacklist.add(member.id)
        await interaction.response.send_message(f"✅ {member.mention} has been added to the blacklist.")
        await self.log_to_channel(interaction.guild, BLACKLIST_LOG_CHANNEL_ID, f"⚠️ {member.mention} manually blacklisted by {interaction.user.mention}.")

    @app_commands.command(name="unblacklist", description="Remove a member from the blacklist.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unblacklist(self, interaction: discord.Interaction, member: discord.Member):
        if member.id in self.blacklist:
            self.blacklist.remove(member.id)
            await interaction.response.send_message(f"✅ {member.mention} has been removed from the blacklist.")
            await self.log_to_channel(interaction.guild, BLACKLIST_LOG_CHANNEL_ID, f"✅ {member.mention} manually removed from blacklist by {interaction.user.mention}.")
        else:
            await interaction.response.send_message(f"❌ {member.mention} is not on the blacklist.")

    # Call this method when applying a timeout to a member
    async def apply_timeout(self, member: discord.Member):
        guild = member.guild
        self.add_timeout(member.id)
        count = self.count_recent_timeouts(member.id)

        if count >= MAX_TIMEOUTS_BEFORE_BLACKLIST:
            self.blacklist.add(member.id)
            await self.log_to_channel(guild, BLACKLIST_LOG_CHANNEL_ID, f"⚠️ {member.mention} automatically blacklisted after {count} timeouts.")
            try:
                await member.send(f"⚠️ You have been blacklisted due to multiple timeouts.")
            except discord.Forbidden:
                pass
            await member.kick(reason="Blacklisted due to multiple timeouts")
        else:
            await self.log_to_channel(guild, TIMEOUT_LOG_CHANNEL_ID, f"⏰ {member.mention} received a timeout ({count}/{MAX_TIMEOUTS_BEFORE_BLACKLIST}).")
            try:
                await member.send(f"⏰ You received a timeout for {TIMEOUT_DURATION_DAYS} days.")
            except discord.Forbidden:
                pass
            # Implement any additional timeout actions here (kick, mute, etc.)

async def setup(bot):
    await bot.add_cog(TimeoutBlacklist(bot))
