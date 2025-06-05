import discord
from discord import app_commands
from discord.ext import commands

# ✅ Kanaal-ID voor get-invite
INVITE_CHANNEL_ID = 1380173141506129942

# ✅ Emoji die gebruikt wordt voor reactie
INVITE_EMOJI = "🔑"

# ✅ Tekst van het invitebericht
INVITE_MESSAGE_TEXT = (
    "Klik op de 🔑 hieronder om een **eenmalige invite link** te ontvangen via DM.\n"
    "Alleen gebruikers met de rol `Voucher` kunnen dit gebruiken."
)

class InvitePost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setupinvitemessage", description="Plaats het invitebericht met reactieknop.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_invite_message(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(INVITE_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("❌ Invitekanaal niet gevonden.", ephemeral=True)
            return

        # Stuur het invitebericht
        message = await channel.send(INVITE_MESSAGE_TEXT)

        # Voeg emoji toe
        await message.add_reaction(INVITE_EMOJI)

        # Bevestiging terugsturen
        await interaction.response.send_message(
            f"✅ Invitebericht succesvol geplaatst in {channel.mention}.", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(InvitePost(bot))
