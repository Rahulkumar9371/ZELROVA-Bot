import discord
from discord.ext import commands

from database import db


WELCOME_MESSAGE = """
👋 Welcome {member} to **{server}**!

Read the rules, choose your roles, and enjoy the ZELROVA community.
"""


LEAVE_MESSAGE = """
👋 **{member}** left the server.
We hope to see them again.
"""


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        db.increment_stat(member.guild.id, "joins")

        channel = discord.utils.get(member.guild.text_channels, name="welcome")

        if channel:
            message = WELCOME_MESSAGE.format(
                member=member.mention,
                server=member.guild.name
            )

            embed = self.embed(
                "🎉 Welcome!",
                message
            )

            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Powered by ZELROVA")

            await channel.send(embed=embed)

        try:
            dm_embed = self.embed(
                f"Welcome to {member.guild.name}",
                "Thanks for joining! Please read the rules and enjoy the server."
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="leave")

        if channel:
            message = LEAVE_MESSAGE.format(
                member=str(member)
            )

            embed = self.embed(
                "Member Left",
                message
            )

            embed.set_thumbnail(url=member.display_avatar.url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            channel = discord.utils.get(after.guild.text_channels, name="boosts")

            if channel:
                embed = self.embed(
                    "🚀 Server Boosted!",
                    f"Thank you {after.mention} for boosting **{after.guild.name}**!"
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                await channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        embed = self.embed(
            "👋 Welcome System",
            "Welcome card, leave card, welcome DM and boost message are ready."
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setautorole(self, ctx, role: discord.Role):
        server = db.get_server(ctx.guild.id)
        server["autorole"] = role.id
        db.update_server(ctx.guild.id, server)

        embed = self.embed(
            "✅ Auto Role Saved",
            f"New members will receive {role.mention}."
        )
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_member_join_autorole(self, member):
        server = db.get_server(member.guild.id)
        role_id = server.get("autorole")

        if not role_id:
            return

        role = member.guild.get_role(role_id)

        if role:
            try:
                await member.add_roles(role)
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(Welcome(bot))