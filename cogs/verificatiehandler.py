import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta

# Role IDs
TRANSPORTER_ROLE_ID = 1380179952665759827
VOUCHER_ROLE_ID = 1380179951155941388

# Log channel IDs
BLACKLIST_LOG_CHANNEL_ID = 1380179997515317279
VOUCH_LOG_CHANNEL_ID = 1380179994357006428

CONFIRMATION_TIMEOUT_MINUTES = 10

class VerificationHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_verification = {}  # user_id -> {inviter, joined_at, attempts, channel_id}
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
        timeout_cog = self.bot.get_cog("TimeoutBlacklist")

        if timeout_cog:
            if member.id in timeout_cog.blacklist:
                try:
                    await member.send("🚫 You are blacklisted from this server.")
                except discord.Forbidden:
                    pass
                await member.kick(reason="Blacklisted user")
                return

            if timeout_cog.has_active_timeout(member.id):
                try:
                    await member.send("⏰ You are currently under a timeout and cannot rejoin yet.")
                except discord.Forbidden:
                    pass
                await member.kick(reason="Active timeout")
                return

        # Check if join came from bot-generated invite
        invites = await guild.invites()
        invite_cog = self.bot.get_cog("InviteManager")
        inviter_id = None

        for invite in invites:
            if invite.code in invite_cog.active_invites:
                inviter_id = invite_cog.active_invites[invite.code]["inviter_id"]
                invite_cog.active_invites[invite.code]["used"] = True
                break

        if inviter_id is None:
            try:
                await member.send("❌ You joined using an unauthorized invite. Only bot-issued invites are allowed.")
            except discord.Forbidden:
                pass
            await self.log_to_channel(guild, VOUCH_LOG_CHANNEL_ID,
                f"⚠️ {member.mention} attempted to join via a non-bot invite and was removed.")
            await member.kick(reason="Non-bot invite used")
            return

        # Create private verification channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        inviter = guild.get_member(inviter_id)
        if inviter:
            overwrites[inviter] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel_name = f"verify-{member.name}".lower().replace(" ", "-")
        verify_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

        self.pending_verification[member.id] = {
            "inviter": inviter_id,
            "joined_at": datetime.utcnow(),
            "attempts": 1,
            "channel_id": verify_channel.id
        }

        await verify_channel.send(
            f"🆕 New member: {member.mention}\nVoucher: <@{inviter_id}>\n\n"
            f"<@{inviter_id}>, please confirm this user by reacting ✅ to this message."
        )
        prompt = await verify_channel.send("React with ✅ to confirm the new member.")
        await prompt.add_reaction("✅")

    @tasks.loop(seconds=60)
    async def cleanup_loop(self):
        now = datetime.utcnow()
        timeout_cog = self.bot.get_cog("TimeoutBlacklist")
        for user_id, data in list(self.pending_verification.items()):
            if now - data["joined_at"] > timedelta(minutes=CONFIRMATION_TIMEOUT_MINUTES):
                guild = discord.utils.get(self.bot.guilds)
                member = guild.get_member(user_id)
                inviter = guild.get_member(data["inviter"]) if data["inviter"] else None

                # Kick and DM the user
                if member:
                    try:
                        await member.send("⌛ You were removed from the server due to no confirmation.")
                    except discord.Forbidden:
                        pass
                    await member.kick(reason="Unverified")

                # Timeout instead of blacklist
                if timeout_cog:
                    timeout_cog.apply_timeout(user_id)

                # Notify the inviter
                if inviter:
                    try:
                        await inviter.send(
                            "⚠️ The player you invited was not verified in time and has been removed.\n"
                            "Please only invite someone when you're ready to vouch for them quickly."
                        )
                    except discord.Forbidden:
                        pass

                # Cleanup channel
                channel = guild.get_channel(data["channel_id"])
                if channel:
                    await channel.delete(reason="Verification expired")

                del self.pending_verification[user_id]

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
        for uid, info in self.pending_verification.items():
            if info["channel_id"] == payload.channel_id:
                data = info
                verified_user_id = uid
                break

        if not data:
            return

        if member.id != data["inviter"]:
            channel = guild.get_channel(payload.channel_id)
            if channel:
                await channel.send("❌ Only the voucher may confirm this user.")
            return

        verified_user = guild.get_member(verified_user_id)
        if verified_user:
            transporter_role = guild.get_role(TRANSPORTER_ROLE_ID)
            if transporter_role:
                await verified_user.add_roles(transporter_role, reason="Voucher confirmed")

            try:
                await verified_user.send("✅ You have been verified and granted access!")
            except discord.Forbidden:
                pass

        channel = guild.get_channel(payload.channel_id)
        if channel:
            await channel.delete(reason="Verification complete")

        del self.pending_verification[verified_user_id]

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unblacklist(self, ctx, member: discord.Member):
        timeout_cog = self.bot.get_cog("TimeoutBlacklist")
        if timeout_cog and member.id in timeout_cog.blacklist:
            timeout_cog.blacklist.remove(member.id)
            await ctx.send(f"✅ {member.name} has been removed from the blacklist.")
        else:
            await ctx.send("❌ This user is not blacklisted.")

async def setup(bot):
    await bot.add_cog(VerificationHandler(bot))
