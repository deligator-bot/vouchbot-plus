import discord
from discord.ext import commands

INVITE_CHANNEL_NAME = "get-invite"
INVITE_EMOJI = "🔑"  # sleutel emoji
INVITE_MESSAGE_TEXT = (
    "Klik op de 🔑 hieronder om een **eenmalige invite link** te ontvangen via DM."
    "\nAlleen gebruikers met de `voucher`-rol kunnen dit gebruiken."
)

class InvitePost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(name="setupinvitemessage")
    async def setup_invite_message(self, ctx):
        """Plaatst het vaste invitebericht met emoji-reactie."""
        channel = discord.utils.get(ctx.guild.text_channels, name=INVITE_CHANNEL_NAME)
        if not channel:
            await ctx.send(f"Kanaal `#{INVITE_CHANNEL_NAME}` niet gevonden.")
            return

        msg = await channel.send(INVITE_MESSAGE_TEXT)
        await msg.add_reaction(INVITE_EMOJI)
        await ctx.send("✅ Invitebericht geplaatst in #{0}.".format(INVITE_CHANNEL_NAME))

async def setup(bot):
    await bot.add_cog(InvitePost(bot))
