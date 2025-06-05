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

    @app_commands.command(name="strikevoucher", description="Geef een voucher een fout (strike).")
    @app_commands.checks.has_permissions(administrator=True)
    async def strike_voucher(self, interaction: discord.Interaction, member: discord.Member):
        if member.id not in self.strikes:
            self.strikes[member.id] = 0
        self.strikes[member.id] += 1

        await interaction.response.send_message(f"⚠️ {member.mention} heeft nu {self.strikes[member.id]} strike(s).", ephemeral=False)
        await self.log_to_channel(interaction.guild, f"⚠️ {member.mention} kreeg een strike van {interaction.user.mention}. Totaal: {self.strikes[member.id]}")

    @app_commands.command(name="checkvouch", description="Bekijk wie iemand heeft geinvite en hoeveel fouten die voucher heeft.")
    async def check_vouch(self, interaction: discord.Interaction, member: discord.Member):
        # Zoek wie de voucher was (uit de invite logs)
        invite_cog = self.bot.get_cog("InviteManager")
        inviter_id = None
        for code, data in invite_cog.active_invites.items():
            if data.get("used") and data.get("inviter_id"):
                if member.id in [m.id for m in interaction.guild.members if m.joined_at and m.joined_at.timestamp()]:
                    inviter_id = data["inviter_id"]
                    break

        if not inviter_id:
            await interaction.response.send_message("❌ Geen voucher gevonden voor deze gebruiker.", ephemeral=True)
            return

        inviter = interaction.guild.get_member(inviter_id)
        strikes = self.strikes.get(inviter_id, 0)

        view = StrikeButtonView(self, inviter)
        await interaction.response.send_message(
            f"👤 {member.mention} is geinvite door {inviter.mention}.
⚠️ Deze voucher heeft {strikes} strike(s).",
            view=view
        )

class StrikeButtonView(discord.ui.View):
    def __init__(self, cog, target_member):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_member = target_member

    @discord.ui.button(label="Geef extra strike ❌", style=discord.ButtonStyle.danger)
    async def give_strike(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ Alleen admins kunnen strikes geven.", ephemeral=True)
            return

        if self.target_member.id not in self.cog.strikes:
            self.cog.strikes[self.target_member.id] = 0
        self.cog.strikes[self.target_member.id] += 1

        await interaction.response.send_message(
            f"⚠️ {self.target_member.mention} kreeg een extra strike. Totaal nu: {self.cog.strikes[self.target_member.id]}",
            ephemeral=False
        )
        await self.cog.log_to_channel(interaction.guild, f"⚠️ {self.target_member.mention} kreeg een extra strike via knop door {interaction.user.mention}. Totaal: {self.cog.strikes[self.target_member.id]}")

async def setup(bot):
    await bot.add_cog(VoucherReputation(bot))
