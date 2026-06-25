import discord
from discord.ext import commands

from database import db


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def mod_embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        data = db.load()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in data:
            data[guild_id] = {}

        if "warnings" not in data:
            data["warnings"] = {}

        if guild_id not in data["warnings"]:
            data["warnings"][guild_id] = {}

        if user_id not in data["warnings"][guild_id]:
            data["warnings"][guild_id][user_id] = []

        data["warnings"][guild_id][user_id].append({
            "reason": reason,
            "moderator": str(ctx.author),
            "moderator_id": ctx.author.id
        })

        db.save(data)

        embed = self.mod_embed(
            "⚠️ User Warned",
            f"{member.mention} has been warned.\n\n**Reason:** {reason}"
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        data = db.load()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        warns = data.get("warnings", {}).get(guild_id, {}).get(user_id, [])

        if not warns:
            await ctx.reply(f"✅ {member.mention} has no warnings.")
            return

        description = ""

        for index, warn in enumerate(warns, start=1):
            description += f"**{index}.** {warn['reason']} — `{warn['moderator']}`\n"

        embed = self.mod_embed(
            f"Warnings for {member}",
            description
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)

        db.increment_stat(ctx.guild.id, "warnings")

        embed = self.mod_embed(
            "👢 User Kicked",
            f"{member.mention} was kicked.\n\n**Reason:** {reason}"
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)

        db.increment_stat(ctx.guild.id, "bans")

        embed = self.mod_embed(
            "🔨 User Banned",
            f"{member.mention} was banned.\n\n**Reason:** {reason}"
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        embed = self.mod_embed(
            "✅ User Unbanned",
            f"`{user}` has been unbanned."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
        duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)

        embed = self.mod_embed(
            "⏳ User Timed Out",
            f"{member.mention} timed out for **{minutes} minutes**.\n\n**Reason:** {reason}"
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None)

        embed = self.mod_embed(
            "✅ Timeout Removed",
            f"{member.mention} timeout removed."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        if amount > 100:
            amount = 100

        deleted = await ctx.channel.purge(limit=amount + 1)

        embed = self.mod_embed(
            "🧹 Messages Purged",
            f"Deleted **{len(deleted) - 1}** messages."
        )

        await ctx.send(embed=embed, delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 5):
        await ctx.channel.edit(slowmode_delay=seconds)

        embed = self.mod_embed(
            "🐢 Slowmode Updated",
            f"Slowmode set to **{seconds} seconds**."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = self.mod_embed(
            "🔒 Channel Locked",
            "Members can no longer send messages here."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = self.mod_embed(
            "🔓 Channel Unlocked",
            "Members can send messages again."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nickname=None):
        await member.edit(nick=nickname)

        embed = self.mod_embed(
            "🏷️ Nickname Updated",
            f"{member.mention}'s nickname has been updated."
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))