import asyncio
import datetime
import discord
from discord.ext import commands

from database import db
from config import Config


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def mod_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "moderation", f"{title} | {description}")
        except Exception:
            pass

        channel = discord.utils.get(guild.text_channels, name="zelrova-logs")

        if channel:
            await channel.send(embed=self.embed(title, description))

    def can_moderate(self, ctx, member):
        if member == ctx.author:
            return False, "❌ Tum khud par action nahi kar sakte."

        if member == ctx.guild.owner:
            return False, "❌ Server owner par action nahi kar sakte."

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return False, "❌ Is member ka role tumse same ya higher hai."

        if ctx.guild.me and member.top_role >= ctx.guild.me.top_role:
            return False, "❌ Mera role is member se neeche hai."

        return True, None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        ok, msg = self.can_moderate(ctx, member)
        if not ok:
            await ctx.reply(msg)
            return

        warning = db.add_warning(
            ctx.guild.id,
            member.id,
            reason,
            ctx.author.id
        )

        warnings = db.get_warnings(ctx.guild.id, member.id)

        embed = self.embed(
            "⚠️ Warning Added",
            (
                f"**User:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** {reason}\n"
                f"**Total Warnings:** {len(warnings)}"
            )
        )

        await ctx.reply(embed=embed)

        await self.mod_log(
            ctx.guild,
            "Warn Log",
            f"{member} warned by {ctx.author}. Reason: {reason}"
        )

        if len(warnings) >= Config.MAX_WARNINGS:
            try:
                duration = discord.utils.utcnow() + datetime.timedelta(minutes=Config.DEFAULT_TIMEOUT_MINUTES)
                await member.timeout(duration, reason="Max warnings reached")

                await ctx.send(
                    embed=self.embed(
                        "⏳ Auto Timeout",
                        f"{member.mention} reached max warnings and was timed out for {Config.DEFAULT_TIMEOUT_MINUTES} minutes."
                    )
                )
            except Exception:
                pass

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        warnings = db.get_warnings(ctx.guild.id, member.id)

        if not warnings:
            await ctx.reply(f"✅ {member.mention} ke paas koi warning nahi hai.")
            return

        description = ""

        for index, warning in enumerate(warnings, start=1):
            description += (
                f"**#{index}** {warning.get('reason', 'No reason')}\n"
                f"Moderator ID: `{warning.get('moderator_id')}`\n"
                f"Time: `{warning.get('time')}`\n\n"
            )

        await ctx.reply(
            embed=self.embed(
                f"⚠️ Warnings for {member}",
                description[:4000]
            )
        )

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        db.clear_warnings(ctx.guild.id, member.id)

        await ctx.reply(
            embed=self.embed(
                "✅ Warnings Cleared",
                f"{member.mention} ki warnings clear kar di gayi."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Clear Warnings",
            f"{member} warnings cleared by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        ok, msg = self.can_moderate(ctx, member)
        if not ok:
            await ctx.reply(msg)
            return

        await member.kick(reason=reason)
        db.increment_stat(ctx.guild.id, "kicks")

        await ctx.reply(
            embed=self.embed(
                "👢 Member Kicked",
                f"**User:** {member}\n**Moderator:** {ctx.author}\n**Reason:** {reason}"
            )
        )

        await self.mod_log(
            ctx.guild,
            "Kick Log",
            f"{member} kicked by {ctx.author}. Reason: {reason}"
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        ok, msg = self.can_moderate(ctx, member)
        if not ok:
            await ctx.reply(msg)
            return

        await member.ban(reason=reason)
        db.increment_stat(ctx.guild.id, "bans")

        await ctx.reply(
            embed=self.embed(
                "🔨 Member Banned",
                f"**User:** {member}\n**Moderator:** {ctx.author}\n**Reason:** {reason}"
            )
        )

        await self.mod_log(
            ctx.guild,
            "Ban Log",
            f"{member} banned by {ctx.author}. Reason: {reason}"
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason="No reason provided"):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)

        await ctx.reply(
            embed=self.embed(
                "✅ Member Unbanned",
                f"**User:** {user}\n**Moderator:** {ctx.author}\n**Reason:** {reason}"
            )
        )

        await self.mod_log(
            ctx.guild,
            "Unban Log",
            f"{user} unbanned by {ctx.author}. Reason: {reason}"
        )

    @commands.command(aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        if amount < 1:
            await ctx.reply("❌ Amount 1 se kam nahi ho sakta.")
            return

        if amount > Config.MAX_PURGE:
            amount = Config.MAX_PURGE

        deleted = await ctx.channel.purge(limit=amount + 1)

        msg = await ctx.send(
            embed=self.embed(
                "🧹 Messages Cleared",
                f"Deleted **{len(deleted) - 1}** messages."
            )
        )

        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass

        await self.mod_log(
            ctx.guild,
            "Clear Log",
            f"{len(deleted) - 1} messages cleared by {ctx.author} in {ctx.channel}"
        )

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int = 10, *, reason="No reason provided"):
        ok, msg = self.can_moderate(ctx, member)
        if not ok:
            await ctx.reply(msg)
            return

        if minutes < 1:
            await ctx.reply("❌ Timeout minimum 1 minute ka hona chahiye.")
            return

        if minutes > 40320:
            await ctx.reply("❌ Timeout max 28 days ka ho sakta hai.")
            return

        duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)

        await ctx.reply(
            embed=self.embed(
                "⏳ Member Timed Out",
                f"**User:** {member.mention}\n**Duration:** {minutes} minutes\n**Reason:** {reason}"
            )
        )

        await self.mod_log(
            ctx.guild,
            "Timeout Log",
            f"{member} timed out by {ctx.author} for {minutes} minutes. Reason: {reason}"
        )

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.timeout(None, reason=reason)

        await ctx.reply(
            embed=self.embed(
                "✅ Timeout Removed",
                f"{member.mention} ka timeout remove kar diya gaya."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Untimeout Log",
            f"{member} timeout removed by {ctx.author}. Reason: {reason}"
        )

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 5):
        if seconds < 0:
            seconds = 0

        if seconds > 21600:
            seconds = 21600

        await ctx.channel.edit(slowmode_delay=seconds)

        await ctx.reply(
            embed=self.embed(
                "🐢 Slowmode Updated",
                f"Slowmode set to **{seconds} seconds**."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Slowmode Log",
            f"Slowmode set to {seconds}s in {ctx.channel} by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await ctx.reply(
            embed=self.embed(
                "🔒 Channel Locked",
                "Members can no longer send messages here."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Lock Log",
            f"{ctx.channel} locked by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await ctx.reply(
            embed=self.embed(
                "🔓 Channel Unlocked",
                "Members can send messages again."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Unlock Log",
            f"{ctx.channel} unlocked by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nickname=None):
        ok, msg = self.can_moderate(ctx, member)
        if not ok:
            await ctx.reply(msg)
            return

        await member.edit(nick=nickname)

        await ctx.reply(
            embed=self.embed(
                "🏷 Nickname Updated",
                f"{member.mention}'s nickname updated."
            )
        )

        await self.mod_log(
            ctx.guild,
            "Nickname Log",
            f"{member} nickname changed by {ctx.author}"
        )

    @commands.command()
    async def moderation(self, ctx):
        embed = self.embed(
            "🛡 ZELROVA Moderation",
            (
                "`!warn @user reason`\n"
                "`!warnings @user`\n"
                "`!clearwarnings @user`\n"
                "`!kick @user reason`\n"
                "`!ban @user reason`\n"
                "`!unban user_id reason`\n"
                "`!timeout @user minutes reason`\n"
                "`!untimeout @user`\n"
                "`!clear amount` or `!purge amount`\n"
                "`!slowmode seconds`\n"
                "`!lock`\n"
                "`!unlock`\n"
                "`!nickname @user name`"
            )
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))