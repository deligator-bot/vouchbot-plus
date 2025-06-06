import discord
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
        bot.loop.create_task(self.send_invite_message())

    async def send_invite_message(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(INVITE_CHANNEL_ID)

        if not channel:
            print("❌ Invite channel not found.")
            return

        try:
            # Controleer of bericht al bestaat (optioneel)
            async for msg in channel.history(limit=10):
                if msg.author == self.bot.user and INVITE_MESSAGE_TEXT in msg.content:
                    print("ℹ️ Invite message already exists. Skipping.")
                    return

            message = await channel.send(INVITE_MESSAGE_TEXT)
            await message.add_reaction(INVITE_EMOJI)
            print("✅ Invite message sent with reaction.")
        except Exception as e:
            print(f"❌ Error while sending invite message: {e}")

async def setup(bot):
    await bot.add_cog(InvitePost(bot))
