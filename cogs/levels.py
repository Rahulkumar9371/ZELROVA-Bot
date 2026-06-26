import random
import datetime
import discord
from discord.ext import commands

from database import db


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = set()

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    def required_xp(self, level):
        return level * 100

    async def level_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "levels", f"{title} | {description}")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            return

        server = db.get_server(message.guild.id)

        if not server.get("modules", {}).get("levels", True):
            return

        settings = server.get("levels", {})

        if not settings.get("enabled", True):
            return

        key = f"{message.guild.id}-{message.author.id}"

        if key in self.cooldowns:
            return

        self.cooldowns.add(key)

        user = db.get_guild_user(message.guild.id, message.author.id)

        xp_min = settings.get("xp_min", 10)
        xp_max = settings.get("xp_max", 25)

        xp_gain = random.randint(xp_min, xp_max)
        coin_gain = random.randint(1, 5)

        user["xp"] += xp_gain
        user["coins"] += coin_gain

        needed = self.required_xp(user["level"])

        if user["xp"] >= needed:
            user["xp"] -= needed
            user["level"] += 1

            await message.channel.send(
                embed=self.embed(
                    "🎉 Level Up!",
                    f"{message.author.mention} reached **Level {user['level']}**!"
                )
            )

            await self.level_log(
                message.guild,
                "Level Up",
                f"{message.author} reached level {user['level']}"
            )

        db.update_guild_user(message.guild.id, message.author.id, user)

        async def remove_cooldown():
            import asyncio
            await asyncio.sleep(settings.get("cooldown", 60))
            self.cooldowns.discard(key)

        self.bot.loop.create_task(remove_cooldown())

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_guild_user(ctx.guild.id, member.id)

        needed = self.required_xp(user["level"])

        embed = self.embed(
            f"📊 {member.name}'s Rank",
            "ZELROVA level profile"
        )

        embed.add_field(name="Level", value=user["level"], inline=True)
        embed.add_field(name="XP", value=f"{user['xp']} / {needed}", inline=True)
        embed.add_field(name="Coins", value=user["coins"], inline=True)

        embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_guild_user(ctx.guild.id, member.id)

        await ctx.reply(
            embed=self.embed(
                "🪙 Balance",
                f"{member.mention} has **{user['coins']} coins**."
            )
        )

    @commands.command()
    async def daily(self, ctx):
        user = db.get_guild_user(ctx.guild.id, ctx.author.id)
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        if user.get("last_daily") == today:
            await ctx.reply("❌ Tumne aaj ka daily reward already claim kar liya.")
            return

        server = db.get_server(ctx.guild.id)
        settings = server.get("levels", {})

        reward = random.randint(
            settings.get("daily_min", 100),
            settings.get("daily_max", 250)
        )

        user["coins"] += reward
        user["last_daily"] = today

        if "Daily Reward" not in user["achievements"]:
            user["achievements"].append("Daily Reward")

        db.update_guild_user(ctx.guild.id, ctx.author.id, user)

        await ctx.reply(
            embed=self.embed(
                "🎁 Daily Reward",
                f"{ctx.author.mention} claimed **{reward} coins**!"
            )
        )

    @commands.command()
    async def leaderboard(self, ctx):
        data = db.load()
        users = data.get("users", {})

        guild_prefix = f"{ctx.guild.id}-"

        guild_users = {
            key: value
            for key, value in users.items()
            if key.startswith(guild_prefix)
        }

        sorted_users = sorted(
            guild_users.items(),
            key=lambda item: (item[1].get("level", 1), item[1].get("xp", 0)),
            reverse=True
        )[:10]

        if not sorted_users:
            await ctx.reply("No leaderboard data yet.")
            return

        description = ""

        for index, (key, info) in enumerate(sorted_users, start=1):
            user_id = int(key.split("-")[1])
            member = ctx.guild.get_member(user_id)
            name = member.mention if member else f"`{user_id}`"

            description += (
                f"**#{index}** {name} — "
                f"Level **{info.get('level', 1)}** | "
                f"XP **{info.get('xp', 0)}** | "
                f"Coins **{info.get('coins', 0)}**\n"
            )

        await ctx.reply(
            embed=self.embed(
                "🏆 ZELROVA Leaderboard",
                description
            )
        )

    @commands.command()
    async def shop(self, ctx):
        embed = self.embed(
            "🛒 ZELROVA Shop",
            (
                "**Coming soon items:**\n"
                "🎨 Color Roles\n"
                "🏷 Custom Badges\n"
                "⭐ Profile Frames\n"
                "🎁 Server Perks\n"
                "💎 Premium Items"
            )
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_guild_user(ctx.guild.id, member.id)

        items = user.get("inventory", [])

        description = "\n".join(items) if items else "Inventory empty."

        await ctx.reply(
            embed=self.embed(
                f"🎒 {member.name}'s Inventory",
                description
            )
        )

    @commands.command()
    async def achievements(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_guild_user(ctx.guild.id, member.id)

        achievements = user.get("achievements", [])

        description = "\n".join([f"🏅 {a}" for a in achievements]) if achievements else "No achievements yet."

        await ctx.reply(
            embed=self.embed(
                f"🏅 {member.name}'s Achievements",
                description
            )
        )

    @commands.command()
    async def levels(self, ctx):
        await ctx.reply(
            embed=self.embed(
                "📊 ZELROVA Levels",
                (
                    "`!rank` — Check rank\n"
                    "`!leaderboard` — Server leaderboard\n"
                    "`!balance` — Check coins\n"
                    "`!daily` — Claim daily reward\n"
                    "`!shop` — View shop\n"
                    "`!inventory` — View inventory\n"
                    "`!achievements` — View achievements"
                )
            )
        )


async def setup(bot):
    await bot.add_cog(Levels(bot))