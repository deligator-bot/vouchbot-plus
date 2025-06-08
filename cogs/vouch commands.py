import discord
from discord.ext import commands
from discord import app_commands

class VouchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="getinvite", description="Generate a unique invite link for a new member.")
    @app_commands.describe(member="The person you want to invite")
    async def get_invite(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        inviter = interaction.user

        # Invite aanmaken
        channel = discord.utils.get(guild.text_channels, id=1380179968406982676)  # #get-invite
        invite = await channel.create_invite(max_uses=1, max_age=3600, unique=True)
        
        # DM sturen in het Engels
        try:
            await member.send(
                f"Hello {member.name},\n\nYou’ve been invited to join the server by {inviter.name}.\n"
                f"Click this link to join (valid for 1 hour, 1 use only):\n{invite.url}\n\n"
                "Please make sure your voucher is online to verify you within 10 minutes. "
                "If no verification happens in time, you'll be removed automatically for safety reasons."
            )
        except discord.Forbidden:
            await interaction.response.send_message("I couldn’t send a DM to that user. Please make sure their DMs are open.", ephemeral=True)
            return

        # Bericht posten in #get-invite
        embed = discord.Embed(
            title="New Invite Generated",
            description=f"{inviter.mention} has created an invite for {member.mention}.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)

        # Reactie naar degene die het commando gebruikte
        await interaction.response.send_message(f"Invite successfully sent to {member.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VouchCommands(bot))
