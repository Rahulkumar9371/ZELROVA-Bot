import discord
from discord.ext import commands


class Security(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    # ===============================
    # JOIN LOCK
    # ===============================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def joinlock(self, ctx):

        embed = self.embed(
            "🔒 Join Lock Enabled",
            "New members will not be allowed until Join Lock is disabled."
        )

        await ctx.reply(embed=embed)

    # ===============================
    # UNLOCK
    # ===============================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def joinunlock(self, ctx):

        embed = self.embed(
            "🔓 Join Lock Disabled",
            "New members can join again."
        )

        await ctx.reply(embed=embed)

    # ===============================
    # VERIFICATION
    # ===============================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def verification(self, ctx):

        embed = self.embed(
            "✅ Verification Enabled",
            "Verification system is now active."
        )

        await ctx.reply(embed=embed)

    # ===============================
    # LOCKDOWN
    # ===============================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):

        for channel in ctx.guild.text_channels:

            overwrite = channel.overwrites_for(ctx.guild.default_role)

            overwrite.send_messages = False

            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite
            )

        embed = self.embed(
            "🚨 Lockdown Enabled",
            "All text channels have been locked."
        )

        await ctx.reply(embed=embed)

    # ===============================
    # UNLOCKDOWN
    # ===============================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unlockdown(self, ctx):

        for channel in ctx.guild.text_channels:

            overwrite = channel.overwrites_for(ctx.guild.default_role)

            overwrite.send_messages = None

            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite
            )

        embed = self.embed(
            "✅ Lockdown Disabled",
            "All text channels are unlocked."
        )

        await ctx.reply(embed=embed)

    # ===============================
    # SERVER STATUS
    # ===============================

    @commands.command()
    async def security(self, ctx):

        embed = discord.Embed(
            title="🛡 ZELROVA Security",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Anti Raid",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Anti Bot",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Verification",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Join Lock",
            value="🟢 Ready",
            inline=False
        )

        embed.add_field(
            name="Channel Protection",
            value="🟢 Ready",
            inline=False
        )

        embed.add_field(
            name="Role Protection",
            value="🟢 Ready",
            inline=False
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Security(bot))