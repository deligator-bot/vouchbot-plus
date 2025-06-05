import discord
from discord.ext import commands
from discord import app_commands

# Log channel ID for strikes
STRIKE_LOG_CHANNEL_ID = 1380180008004347994

class VoucherReputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strikes = {}  # user_id -> int

    async def log_to_channel(self, guild, message):
        channel = guild.get_channel(STRIKE_LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)

    @app_commands.command(name="strikevoucher", description="Assign a strike to a voucher.")
    @app_commands.checks.has_permissions(administrator=True)
    async def strike_voucher(self, interaction: discord.Interaction, member: discord.Member):
        if member.id not in self.strikes:
            self.strikes[member.id] = 0
        self.strikes[member.id] += 1

        await interaction.response.send_message(
            f"⚠️ {member.mention} now has {self.strikes[member.id]} strike(s).",
            ephemeral=False
        )
        await self.log_to_channel(
            interaction.guild,
            f"⚠️ {member.mention} received a strike from {interaction.user.mention}. Total: {self.strikes[member.id]}"
        )

    @app_commands.command(name="checkvouch", description="See who invited a user and how many strikes their voucher has.")
    async def check_vouch(self, interaction: discord.Interaction, member: discord.Member):
        invite_cog = self.bot.get_cog("InviteManager")
        if not invite_cog:
            await interaction.response.send_message("⚠️ InviteManager is not available.", ephemeral=True)
            return

        inviter_id = invite_cog.get_inviter_by_user_id(member.id)
        if not inviter_id:
            await interaction.response.send_message("❌ No voucher found for this user.", ephemeral=True)
            return

        inviter = interaction.guild.get_member(inviter_id)
        if not inviter:
            await interaction.response.send_message("❌ The voucher is no longer in the server.", ephemeral=True)
            return

        strikes = self.strikes.get(inviter_id, 0)

        view = StrikeButtonView(self, inviter)
        await interaction.response.send_message(
            f"👤 {member.mention} was invited by {inviter.mention}.\n"
            f"⚠️ This voucher has {strikes} strike(s).",
            view=view
        )

class StrikeButtonView(discord.ui.View):
    def __init__(self, cog, target_member):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_member = target_member

    @discord.ui.button(label="Assign extra strike ❌", style=discord.ButtonStyle.danger)
    async def give_strike(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ Only admins can assign strikes.", ephemeral=True)
            return

        if self.target_member.id not in self.cog.strikes:
            self.cog.strikes[self.target_member.id] = 0
        self.cog.strikes[self.target_member.id] += 1

        await interaction.response.send_message(
            f"⚠️ {self.target_member.mention} received an extra strike. Total now: {self.cog.strikes[self.target_member.id]}",
            ephemeral=False
        )
        await self.cog.log_to_channel(
            interaction.guild,
            f"⚠️ {self.target_member.mention} received an extra strike via button from {interaction.user.mention}. Total: {self.cog.strikes[self.target_member.id]}"
        )

async def setup(bot):
    await bot.add_cog(VoucherReputation(bot))
