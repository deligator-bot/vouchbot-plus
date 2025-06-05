import discord
from discord import app_commands
from discord.ext import commands
import uuid

# Role & channel IDs
VOUCHER_ROLE_ID = 1380179951155941388
GET_INVITE_CHANNEL_ID = 1380179968406982676
VOUCH_LOG_CHANNEL_ID = 1380179994357006428

class VouchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vouch_mistakes = {}  # voucher_id → aantal fouten

    @app_commands.command(name="checkvouch", description="Bekijk wie deze speler heeft ge-vouched.")
    async def checkvouch(self, interaction: discord.Interaction, member: discord.Member):
        handler = self.bot.get_cog("VerificationHandler")
        data = handler.pending_verification.get(member.id)

        if not data:
            await interaction.response.send_message("❌ Deze speler zit niet in het verificatieproces.", ephemeral=True)
            return

        inviter_id = data["inviter"]
        if not inviter_id:
            await interaction.response.send_message("❓ Geen voucher gevonden voor deze speler.", ephemeral=True)
            return

        embed = discord.Embed(title="Vouch informatie", color=discord.Color.green())
        embed.add_field(name="Voucher", value=f"<@{inviter_id}>", inline=True)
        embed.add_field(name="Lid", value=member.mention, inline=True)
        embed.set_footer(text="Bevestig hieronder als je deze vouch niet vertrouwt.")

        msg = await interaction.response.send_message(embed=embed, ephemeral=False)
        real_msg = await interaction.original_response()
        await real_msg.add_reaction("❌")

        def check(reaction, user):
            return (
                reaction.message.id == real_msg.id
                and str(reaction.emoji) == "❌"
                and user.guild_permissions.administrator
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            self.vouch_mistakes[inviter_id] = self.vouch_mistakes.get(inviter_id, 0) + 1
            await real_msg.reply(f"⚠️ De voucher <@{inviter_id}> heeft nu {self.vouch_mistakes[inviter_id]} strikes.")
        except:
            pass  # Geen reactie ontvangen binnen tijd

    @app_commands.command(name="strikevoucher", description="Geef handmatig een strike aan een voucher.")
    async def strikevoucher(self, interaction: discord.Interaction, member: discord.Member):
        self.vouch_mistakes[member.id] = self.vouch_mistakes.get(member.id, 0) + 1
        await interaction.response.send_message(
            f"⚠️ <@{member.id}> heeft nu {self.vouch_mistakes[member.id]} strike(s).", ephemeral=False
        )

    @app_commands.command(name="getinvite", description="Get a one-time invite link via DM (Voucher only).")
    async def getinvite(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        voucher_role = guild.get_role(VOUCHER_ROLE_ID)
        if voucher_role not in user.roles:
            await interaction.response.send_message(
                "❌ You must have the Voucher role to use this command.", ephemeral=True
            )
            return

        invite_channel = guild.get_channel(GET_INVITE_CHANNEL_ID)
        invite = await invite_channel.create_invite(
            max_uses=1,
            max_age=3600,
            unique=True,
            reason=f"Manual invite requested by {user}"
        )

        try:
            await user.send(
                f"🎫 Here is your unique invite link:\n{invite.url}\nNote: valid for 1 hour and one-time use only."
            )
            await interaction.response.send_message(
                "✅ I've sent you the invite link via DM.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM. Please open your DMs and try again.", ephemeral=True
            )
            return

        log_channel = guild.get_channel(VOUCH_LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📨 {user.mention} requested a manual invite via /getinvite.")

async def setup(bot):
    await bot.add_cog(VouchCommands(bot))
