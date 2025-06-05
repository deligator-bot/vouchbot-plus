import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta

# Role IDs
TRANSPORTER_ROLE_ID = 1380179952665759827  # Transporter role
VOUCHER_ROLE_ID = 1380179951155941388      # Voucher role

# Log channel IDs
BLACKLIST_LOG_CHANNEL_ID = 1380179997515317279
VOUCH_LOG_CHANNEL_ID = 1380179994357006428

# Timeout (in minutes) for verification confirmation
CONFIRMATION_TIMEOUT_MINUTES = 10

class VerificationHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_verification = {}  # user_id -> dict with inviter, joined_at, attempts, channel_id
        self.blacklist = set()
        self.cleanup_loop.start()

    async def log_to_channel(self, guild, channel_id, message):
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        guild = member.guild
        invites = await guild.invites()

        invite_cog = self.bot.get_cog("InviteManager")
        inviter_id = None
        for invite in invites:
            if invite.code in invite_cog.active_invites:
                inviter_id = invite_cog.active_invites[invite.code]["inviter_id"]
                invite_cog.active_invites[invite.code]["used"] = True
                break

        if member.id in self.blacklist:
            try:
                await member.send("🚫 You are blacklisted from this server.")
            except discord.Forbidden:
                pass
            await member.kick(reason="Blacklisted user")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        if inviter_id:
            inviter = guild.get_member(inviter_id)
            if inviter:
                overwrites[inviter] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel_name = f"verify-{member.name}".lower().replace(" ", "-")
        verify_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, reason="Temporary verification channel")

        self.pending_verification[member.id] = {
            "inviter": inviter_id,
            "joined_at": datetime.utcnow(),
            "attempts": 1,
            "channel_id": verify_channel.id
        }

        inviter_mention = f"<@{inviter_id}>" if inviter_id else "Unknown"
        await verify_channel.send(
            f"🆕 New member: {member.mention}\nVoucher: {inviter_mention}\n\n"
            f"{inviter_mention}, please confirm this user by reacting ✅ to this message."
        )

        msg = await verify_channel.send("React with ✅ to confirm the new member.")
        await msg.add_reaction("✅")

    @tasks.loop(seconds=60)
    async def cleanup_loop(self):
        now = datetime.utcnow()
        to_kick = []

        for user_id, data in list(self.pending_verification.items()):
            if now - data["joined_at"] > timedelta(minutes=CONFIRMATION_TIMEOUT_MINUTES):
                to_kick.append(user_id)

        for uid in to_kick:
            guild = discord.utils.get(self.bot.guilds)  # Assuming single guild
            member = guild.get_member(uid) if guild else None
            if member:
                try:
                    await member.send("⌛ You have been removed because you were not verified in time.")
                except discord.Forbidden:
                    pass
                await member.kick(reason="No vouch within time limit.")

                current = self.pending_verification.get(uid)
                if current:
                    if current["attempts"] >= 2:
                        self.blacklist.add(uid)
                        await self.log_to_channel(guild, BLACKLIST_LOG_CHANNEL_ID,
                            f"⚠️ Member {member.name} has been blacklisted due to 2 join attempts without vouch."
                        )

                    channel_id = current.get("channel_id")
                    if channel_id:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            await channel.delete(reason="Verification expired")

            self.pending_verification.pop(uid, None)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name != "✅":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        data = None
        verified_user_id = None
        for user_id, info in self.pending_verification.items():
            if info.get("channel_id") == payload.channel_id:
                data = info
                verified_user_id = user_id
                break

        if not data:
            return

        verified_user = guild.get_member(verified_user_id)
        if not verified_user:
            return

        if member.id != data["inviter"]:
            channel = guild.get_channel(payload.channel_id)
            if channel:
                await channel.send("❌ Only the voucher can confirm this user.")
            return

        transporter_role = guild.get_role(TRANSPORTER_ROLE_ID)
        if transporter_role:
            await verified_user.add_roles(transporter_role, reason="Approved by voucher")

        try:
            await verified_user.send("✅ You have been successfully verified and granted access!")
        except discord.Forbidden:
            pass

        channel = guild.get_channel(payload.channel_id)
        if channel:
            await channel.delete(reason="Verification confirmed")

        self.pending_verification.pop(verified_user_id, None)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unblacklist(self, ctx, member: discord.Member):
        if member.id in self.blacklist:
            self.blacklist.remove(member.id)
            await ctx.send(f"✅ {member.name} has been removed from the blacklist.")
        else:
            await ctx.send("❌ This user is not on the blacklist.")

async def setup(bot):
    await bot.add_cog(VerificationHandler(bot))
