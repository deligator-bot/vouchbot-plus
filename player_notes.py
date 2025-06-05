import discord
from discord.ext import commands
from discord import app_commands

# Kanaal-ID voor het loggen van notities
PLAYER_NOTES_CHANNEL_ID = 1380180005484498996  # Correct kanaal-ID van #player-notes

class PlayerNotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notes = {}  # user_id -> list of (note, author, timestamp)

    async def log_note(self, guild, user: discord.Member, note: str, author: discord.Member):
        channel = guild.get_channel(PLAYER_NOTES_CHANNEL_ID)
        if not channel:
            return
        embed = discord.Embed(
            title=f"📝 Nieuwe notitie voor {user.name}",
            description=note,
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Toegevoegd door: {author.name}")
        await channel.send(embed=embed)

    @app_commands.command(name="addnote", description="Voegt een notitie toe over een speler.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_note(self, interaction: discord.Interaction, member: discord.Member, *, note: str):
        user_id = member.id
        if user_id not in self.notes:
            self.notes[user_id] = []

        self.notes[user_id].append((note, interaction.user.name, discord.utils.utcnow()))
        await interaction.response.send_message(f"✅ Notitie toegevoegd voor {member.name}.", ephemeral=True)
        await self.log_note(interaction.guild, member, note, interaction.user)

    @app_commands.command(name="checknotes", description="Bekijk alle notities over een speler.")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_notes(self, interaction: discord.Interaction, member: discord.Member):
        user_id = member.id
        entries = self.notes.get(user_id, [])
        if not entries:
            await interaction.response.send_message(f"ℹ️ Er zijn nog geen notities over {member.name}.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📄 Notities over {member.name}",
            color=discord.Color.teal()
        )

        for i, (note, author, timestamp) in enumerate(entries, start=1):
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
            embed.add_field(
                name=f"{i}. Toegevoegd door {author} op {formatted_time}",
                value=note,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PlayerNotes(bot))
