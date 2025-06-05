import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

# Log channel ID voor strikes
STRIKE_LOG_CHANNEL_ID = 1380180008004347994

class VoucherReputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vouch_map = {}      # user_id -> voucher_id
        self.strike_counts = {}  # voucher_id -> int

    async def log_to_channel(self, guild, channel_id, message):
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

    def register_vouch(self, user_id, voucher_id):
        self.vouch_map[user_id] = voucher_id

    @app_commands.command(name="checkvouch", description="Bekijk wie iemand heeft gevouched.")
    async def checkvouch(self, interaction: discord.Interaction, member: discord.Member):
        voucher_id = self.vouch_map.get(member.id)

        if not voucher_id:
            await interaction.response.send_message("❌ Geen voucher gevonden voor deze gebruiker.", ephemeral=True)
            return

        voucher_mention = f"<@{voucher_id}>"
        strike_count = self.strike_counts.get(voucher_id, 0)

        embed = discord.Embed(title="Vouch Info", color=discord.Color.blue())
        embed.add_field(name="Gevouchte speler:", value=member.mention, inline=False)
        embed.add_field(name="Voucher:", value=voucher_mention, inline=False)
        embed.set_footer(text=f"Aantal strikes: {strike_count}")

        view = View()

        class ReportButton(Button):
            def __init__(self):
                super().__init__(label="Negatief beoordelen", style=discord.ButtonStyle.danger)

            async def callback(self, interaction_inner: discord.Interaction):
                self.strike_counts[voucher_id] = self.strike_counts.get(voucher_id, 0) + 1
                new_strikes = self.strike_counts[voucher_id]
                await interaction_inner.response.send_message(f"⚠️ Voucher {voucher_mention} heeft nu {new_strikes} strike(s).", ephemeral=False)
                await self.log_to_channel(interaction.guild, STRIKE_LOG_CHANNEL_ID,
                    f"⚠️ {voucher_mention} kreeg een strike via beoordeling. Totaal nu: {new_strikes}.")

        view.add_item(ReportButton())
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="strikevoucher", description="Geef handmatig een strike aan een voucher.")
    @app_commands.checks.has_permissions(administrator=True)
    async def strikevoucher(self, interaction: discord.Interaction, member: discord.Member):
        self.strike_counts[member.id] = self.strike_counts.get(member.id, 0) + 1
        strikes = self.strike_counts[member.id]

        await interaction.response.send_message(f"⚠️ {member.mention} heeft nu {strikes} strike(s).", ephemeral=False)
        await self.log_to_channel(interaction.guild, STRIKE_LOG_CHANNEL_ID,
            f"⚠️ {member.mention} kreeg handmatig een strike. Totaal nu: {strikes}.")

async def setup(bot):
    await bot.add_cog(VoucherReputation(bot))
