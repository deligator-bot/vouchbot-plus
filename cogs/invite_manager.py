import discord
from discord.ext import commands
from discord import app_commands
import uuid

# 📌 Configuratie
GET_INVITE_CHANNEL_ID = 1380179968406982676  # ✅ Jouw juiste get-invite kanaal
VOUCH_LOG_CHANNEL_ID = 1380173161991110786   # ✅ Logkanaal voor vouches
VOUCHER_ROLE_ID = 1380179951155941388        # ✅ Juiste rol-ID voor Vouchers
INVITE_EMOJI = "🔑"

class InviteManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_invites = {}       # invite_code -> metadata
        self.joined_invites = {}       # user_id -> inviter_id

    async def log_to_channel(self, guild, channel_id, message):
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        if payload.channel_id != GET_INVITE_CHANNEL_ID:
            return
        if str(payload.emoji) != INVITE_EMOJI:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        inviter = payload.member

        if not any(role.id == VOUCHER_ROLE_ID for role in inviter.roles):
            return

        unique_id = str(uuid.uuid4())[:8]
        invite = await channel.create_invite(
            max_uses=1,
            max_age=3600,
            unique=True,
            reason=f"Vouch by {inviter}"
        )

        self.active_invites[invite.code] = {
            "inviter_id": inviter.id,
            "used": False,
            "uuid": unique_id
        }

        try:
            await inviter.send(
                f"🎫 Unique invite link generated:\n{invite.url}\nNote: this link is valid for 1 hour and can only be used once."
            )
        except discord.Forbidden:
            await channel.send(f"{inviter.mention}, I couldn't send you a DM. Please enable your DMs.")

        await self.log_to_channel(
            guild,
            VOUCH_LOG_CHANNEL_ID,
            f"📨 {inviter.mention} generated a unique invite (`{invite.code}`) – valid for 1 hour, one-time use."
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        guild = member.guild
        invites = await guild.invites()

        for invite in invites:
            if invite.code in self.active_invites:
                inviter_id = self.active_invites[invite.code]["inviter_id"]
                self.active_invites[invite.code]["used"] = True
                self.joined_invites[member.id] = inviter_id

                inviter = guild.get_member(inviter_id)
                if inviter:
                    try:
                        await inviter.send(
                            f"⚠️ The player who used your invite just joined but hasn't been verified yet.\n"
                            "Please make sure you're online and guide them through the verification process.\n"
                            "Also explain the server rules and what’s expected of new members. Thanks!"
                        )
                    except discord.Forbidden:
                        await self.log_to_channel(
                            guild,
                            VOUCH_LOG_CHANNEL_ID,
                            f"⚠️ Tried to DM {inviter.mention}, but DMs are disabled."
                        )

                    await self.log_to_channel(
                        guild,
                        VOUCH_LOG_CHANNEL_ID,
                        f"🔍 {member.mention} joined using invite from {inviter.mention} (`{invite.code}`)."
                    )
                break

    @app_commands.command(name="getinvite", description="Genereer een unieke vouch-invite")
    async def get_invite(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        channel = guild.get_channel(GET_INVITE_CHANNEL_ID)

        if not any(role.id == VOUCHER_ROLE_ID for role in user.roles):
            await interaction.response.send_message("❌ Je hebt geen toestemming voor dit commando.", ephemeral=True)
            return

        invite = await channel.create_invite(
            max_uses=1,
            max_age=3600,
            unique=True,
            reason=f"Vouch door {user}"
        )

        self.active_invites[invite.code] = {
            "inviter_id": user.id,
            "used": False,
            "uuid": str(uuid.uuid4())[:8]
        }

        try:
            await user.send(
                f"🎫 Invite gegenereerd: {invite.url}\nGeldig voor 1 uur, één keer te gebruiken."
            )
            await interaction.response.send_message("✅ Invite is naar je DM gestuurd!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Invite gegenereerd, maar ik kon je geen DM sturen.", ephemeral=True)

    def get_inviter_by_code(self, code):
        return self.active_invites.get(code)

    def get_inviter_by_user_id(self, user_id):
        return self.joined_invites.get(user_id)

async def setup(bot):
    cog = InviteManager(bot)
    await bot.add_cog(cog)
