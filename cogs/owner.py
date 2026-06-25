import discord
from discord.ext import commands

from config import Config


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, ctx):
        return ctx.author.id == Config.OWNER_ID

    @commands.command()
    async def owner(self, ctx):
        if not self.is_owner(ctx):
            await ctx.reply("❌ This command is owner only.")
            return

        embed = discord.Embed(
            title="👑 ZELROVA Owner Panel",
            description="Owner control commands are active.",
            color=discord.Color.red()
        )

        embed.add_field(name="Bot Status", value="`!setstatus online/idle/dnd`", inline=False)
        embed.add_field(name="Broadcast", value="`!broadcast message`", inline=False)
        embed.add_field(name="Servers", value="`!servers`", inline=False)

        await ctx.reply(embed=embed)

    @commands.command()
    async def setstatus(self, ctx, status="online"):
        if not self.is_owner(ctx):
            await ctx.reply("❌ Owner only.")
            return

        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd
        }

        await self.bot.change_presence(
            status=status_map.get(status, discord.Status.online),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="One Bot. Everything You Need."
            )
        )

        await ctx.reply(f"✅ Bot status changed to `{status}`.")

    @commands.command()
    async def broadcast(self, ctx, *, message=None):
        if not self.is_owner(ctx):
            await ctx.reply("❌ Owner only.")
            return

        if not message:
            await ctx.reply("Use: `!broadcast your message`")
            return

        sent = 0

        for guild in self.bot.guilds:
            channel = guild.system_channel

            if channel:
                try:
                    await channel.send(f"📢 **ZELROVA Broadcast**\n\n{message}")
                    sent += 1
                except Exception:
                    pass

        await ctx.reply(f"✅ Broadcast sent to `{sent}` servers.")

    @commands.command()
    async def servers(self, ctx):
        if not self.is_owner(ctx):
            await ctx.reply("❌ Owner only.")
            return

        description = ""

        for guild in self.bot.guilds:
            description += f"**{guild.name}** — `{guild.id}` — `{guild.member_count}` members\n"

        embed = discord.Embed(
            title="🌐 Connected Servers",
            description=description[:4000] if description else "No servers found.",
            color=discord.Color.red()
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))