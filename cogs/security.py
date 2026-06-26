import datetime
import discord
from discord.ext import commands

from database import db
from config import Config


class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_lock = set()
        self.recent_joins = {}

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def security_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "security", f"{title} | {description}")
        except Exception:
            pass

        channel = discord.utils.get(guild.text_channels, name="zelrova-logs")

        if channel:
            await channel.send(embed=self.embed(title, description))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        if guild.id in self.join_lock:
            try:
                await member.kick(reason="Join lock enabled")
                await self.security_log(
                    guild,
                    "🔒 Join Lock Kick",
                    f"{member} was kicked because join lock is enabled."
                )
            except Exception:
                pass
            return

        now = datetime.datetime.utcnow().timestamp()
        self.recent_joins.setdefault(guild.id, [])
        self.recent_joins[guild.id].append(now)

        self.recent_joins[guild.id] = [
            t for t in self.recent_joins[guild.id]
            if now - t <= 20
        ]

        if len(self.recent_joins[guild.id]) >= 8:
            self.join_lock.add(guild.id)

            await self.security_log(
                guild,
                "🚨 Anti Raid Triggered",
                "Too many members joined quickly. Join lock has been enabled."
            )

        if member.bot:
            await self.security_log(
                guild,
                "🤖 Bot Joined",
                f"Bot joined: {member} (`{member.id}`)"
            )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def joinlock(self, ctx):
        self.join_lock.add(ctx.guild.id)

        await ctx.reply(
            embed=self.embed(
                "🔒 Join Lock Enabled",
                "New members will be kicked until join lock is disabled."
            )
        )

        await self.security_log(
            ctx.guild,
            "Join Lock",
            f"Enabled by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def joinunlock(self, ctx):
        self.join_lock.discard(ctx.guild.id)

        await ctx.reply(
            embed=self.embed(
                "🔓 Join Lock Disabled",
                "New members can join again."
            )
        )

        await self.security_log(
            ctx.guild,
            "Join Unlock",
            f"Disabled by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        locked = 0

        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = False

                await channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=overwrite
                )

                locked += 1
            except Exception:
                pass

        await ctx.reply(
            embed=self.embed(
                "🚨 Lockdown Enabled",
                f"Locked **{locked}** text channels."
            )
        )

        await self.security_log(
            ctx.guild,
            "Lockdown Enabled",
            f"{locked} channels locked by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unlockdown(self, ctx):
        unlocked = 0

        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = None

                await channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=overwrite
                )

                unlocked += 1
            except Exception:
                pass

        await ctx.reply(
            embed=self.embed(
                "✅ Lockdown Disabled",
                f"Unlocked **{unlocked}** text channels."
            )
        )

        await self.security_log(
            ctx.guild,
            "Lockdown Disabled",
            f"{unlocked} channels unlocked by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def verification(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name="Verified")

        if not role:
            try:
                role = await ctx.guild.create_role(
                    name="Verified",
                    reason="ZELROVA verification role"
                )
            except Exception:
                role = None

        await ctx.reply(
            embed=self.embed(
                "✅ Verification System",
                "Verification foundation is ready. Use onboarding panel for full verification flow."
            )
        )

        await self.security_log(
            ctx.guild,
            "Verification",
            f"Verification checked by {ctx.author}"
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.security_log(
            channel.guild,
            "⚠️ Channel Deleted",
            f"Channel deleted: `{channel.name}`"
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.security_log(
            role.guild,
            "⚠️ Role Deleted",
            f"Role deleted: `{role.name}`"
        )

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.security_log(
            channel.guild,
            "⚠️ Webhook Update",
            f"Webhook activity detected in {channel.mention}"
        )

    @commands.command()
    async def security(self, ctx):
        active_join_lock = ctx.guild.id in self.join_lock

        embed = self.embed(
            "🔐 ZELROVA Security Status",
            "Server protection status overview."
        )

        embed.add_field(name="Anti Raid", value="🟢 Active", inline=True)
        embed.add_field(name="Anti Bot Log", value="🟢 Active", inline=True)
        embed.add_field(name="Join Lock", value="🔒 Enabled" if active_join_lock else "🔓 Disabled", inline=True)
        embed.add_field(name="Channel Protection", value="🟢 Logging", inline=True)
        embed.add_field(name="Role Protection", value="🟢 Logging", inline=True)
        embed.add_field(name="Webhook Protection", value="🟢 Logging", inline=True)
        embed.add_field(name="Emergency Lockdown", value="Ready", inline=True)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Security(bot))