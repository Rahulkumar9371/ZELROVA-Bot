import discord
from discord.ext import commands


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_name = "zelrova-logs"

    async def send_log(self, guild, title, description):
        channel = discord.utils.get(guild.text_channels, name=self.log_channel_name)

        if not channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        await self.send_log(
            message.guild,
            "🗑 Message Deleted",
            f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Message:** {message.content}"
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(
            member.guild,
            "📥 Member Joined",
            f"{member.mention} joined the server."
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            member.guild,
            "📤 Member Left",
            f"`{member}` left the server."
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(
            guild,
            "🔨 Member Banned",
            f"`{user}` was banned."
        )

    @commands.command()
    async def logs(self, ctx):
        await ctx.reply("📜 Logs system active. Create a channel named `zelrova-logs`.")


async def setup(bot):
    await bot.add_cog(Logs(bot))