import io
import datetime
import discord
from discord.ext import commands

from database import db


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx, category: str = "all"):
        data = db.load()

        guild_logs = data.get("logs", {}).get(str(ctx.guild.id), {})

        if not guild_logs:
            await ctx.reply("❌ No logs available.")
            return

        text = ""

        if category.lower() == "all":
            for log_type, entries in guild_logs.items():
                text += f"\n========== {log_type.upper()} ==========\n\n"

                for entry in entries:
                    text += (
                        f"[{entry.get('time','Unknown')}]\n"
                        f"{entry.get('message','No message')}\n\n"
                    )

        else:
            entries = guild_logs.get(category.lower())

            if entries is None:
                await ctx.reply("❌ Invalid log category.")
                return

            for entry in entries:
                text += (
                    f"[{entry.get('time','Unknown')}]\n"
                    f"{entry.get('message','No message')}\n\n"
                )

        if not text:
            text = "No logs found."

        if len(text) < 3900:
            await ctx.reply(
                embed=self.embed(
                    "📜 ZELROVA Logs",
                    f"```{text[:3900]}```"
                )
            )
        else:
            buffer = io.BytesIO(text.encode("utf-8"))

            await ctx.reply(
                file=discord.File(
                    buffer,
                    filename=f"{ctx.guild.id}_logs.txt"
                )
            )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearlogs(self, ctx):
        data = db.load()

        data.setdefault("logs", {})
        data["logs"][str(ctx.guild.id)] = {}

        db.save(data)

        await ctx.reply(
            embed=self.embed(
                "🗑 Logs Cleared",
                "All server logs have been deleted."
            )
        )

    @commands.command()
    async def logstats(self, ctx):
        data = db.load()

        guild_logs = data.get("logs", {}).get(str(ctx.guild.id), {})

        total = 0

        embed = self.embed(
            "📊 Log Statistics",
            "Current server log statistics."
        )

        for category, entries in guild_logs.items():
            count = len(entries)
            total += count

            embed.add_field(
                name=category.title(),
                value=str(count),
                inline=True
            )

        embed.add_field(
            name="Total",
            value=str(total),
            inline=False
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def exportlogs(self, ctx):
        data = db.load()

        guild_logs = data.get("logs", {}).get(str(ctx.guild.id), {})

        if not guild_logs:
            await ctx.reply("❌ No logs available.")
            return

        export = ""

        for category, entries in guild_logs.items():

            export += f"\n========== {category.upper()} ==========\n\n"

            for entry in entries:

                export += (
                    f"[{entry.get('time')}]\n"
                    f"{entry.get('message')}\n\n"
                )

        file = discord.File(
            io.BytesIO(export.encode("utf-8")),
            filename=f"zelrova_logs_{ctx.guild.id}.txt"
        )

        await ctx.reply(file=file)

    @commands.command()
    async def loghelp(self, ctx):
        embed = self.embed(
            "📜 ZELROVA Log Commands",
            (
                "`!logs`\n"
                "`!logs moderation`\n"
                "`!logs security`\n"
                "`!logs automod`\n"
                "`!logs tickets`\n"
                "`!logs levels`\n"
                "`!clearlogs`\n"
                "`!logstats`\n"
                "`!exportlogs`"
            )
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))