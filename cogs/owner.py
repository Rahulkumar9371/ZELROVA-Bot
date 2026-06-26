import datetime
import discord
from discord.ext import commands

from config import Config
from database import db


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, ctx):
        return ctx.author.id == Config.OWNER_ID

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def deny(self, ctx):
        await ctx.reply("❌ This command is owner only.")

    @commands.command()
    async def owner(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        embed = self.embed(
            "👑 ZELROVA Owner Panel",
            (
                "`!setstatus online/idle/dnd`\n"
                "`!broadcast message`\n"
                "`!servers`\n"
                "`!reloadcog cog_name`\n"
                "`!syncstate`\n"
                "`!maintenance`\n"
                "`!devmode`\n"
                "`!premiumserver server_id`\n"
                "`!databaseinfo`"
            )
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def setstatus(self, ctx, status="online"):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.invisible
        }

        await self.bot.change_presence(
            status=status_map.get(status, discord.Status.online),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=Config.MISSION
            )
        )

        db.update_bot_state(status=status)

        await ctx.reply(f"✅ Bot status changed to `{status}`.")

    @commands.command()
    async def broadcast(self, ctx, *, message=None):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        if not message:
            await ctx.reply("Use: `!broadcast your message`")
            return

        sent = 0

        for guild in self.bot.guilds:
            channel = guild.system_channel

            if channel:
                try:
                    await channel.send(
                        embed=self.embed(
                            "📢 ZELROVA Broadcast",
                            message
                        )
                    )
                    sent += 1
                except Exception:
                    pass

        await ctx.reply(f"✅ Broadcast sent to `{sent}` servers.")

    @commands.command()
    async def servers(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        description = ""

        for guild in self.bot.guilds:
            description += (
                f"**{guild.name}**\n"
                f"ID: `{guild.id}`\n"
                f"Members: `{guild.member_count}`\n"
                f"Owner ID: `{guild.owner_id}`\n\n"
            )

        embed = self.embed(
            "🌐 Connected Servers",
            description[:4000] if description else "No servers found."
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def reloadcog(self, ctx, cog=None):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        if not cog:
            await ctx.reply("Use: `!reloadcog moderation`")
            return

        extension = f"cogs.{cog}"

        try:
            await self.bot.reload_extension(extension)
            await ctx.reply(f"✅ Reloaded `{extension}`")
        except Exception as e:
            await ctx.reply(f"❌ Failed to reload `{extension}`\n```{e}```")

    @commands.command()
    async def syncstate(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)

        db.update_bot_state(
            status="online",
            servers=len(self.bot.guilds),
            users=total_members
        )

        for guild in self.bot.guilds:
            server = db.get_server(guild.id)
            server["server_name"] = guild.name
            server["server_id"] = str(guild.id)
            server["owner_id"] = str(guild.owner_id)
            server["member_count"] = guild.member_count or 0
            server["icon_url"] = guild.icon.url if guild.icon else None
            server["bot_joined"] = True
            db.update_server(guild.id, server)

        await ctx.reply("✅ Bot state synced with database.")

    @commands.command()
    async def maintenance(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        data = db.load()
        current = data["bot"].get("maintenance", False)
        data["bot"]["maintenance"] = not current
        db.save(data)

        await ctx.reply(f"✅ Maintenance mode: `{not current}`")

    @commands.command()
    async def devmode(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        data = db.load()
        current = data["bot"].get("developer_mode", False)
        data["bot"]["developer_mode"] = not current
        db.save(data)

        await ctx.reply(f"✅ Developer mode: `{not current}`")

    @commands.command()
    async def premiumserver(self, ctx, server_id: int):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        db.add_premium_server(server_id)

        await ctx.reply(f"✅ Server `{server_id}` added to premium list.")

    @commands.command()
    async def databaseinfo(self, ctx):
        if not self.is_owner(ctx):
            await self.deny(ctx)
            return

        data = db.load()

        embed = self.embed(
            "🗄 ZELROVA Database Info",
            (
                f"Servers: `{len(data.get('servers', {}))}`\n"
                f"Users: `{len(data.get('users', {}))}`\n"
                f"Tickets: `{len(data.get('tickets', {}))}`\n"
                f"Warnings: `{len(data.get('warnings', {}))}`\n"
                f"Premium Servers: `{len(data.get('premium', {}).get('servers', []))}`"
            )
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))