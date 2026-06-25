import random
import discord
from discord.ext import commands

from database import db


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = set()

    def level_required_xp(self, level):
        return level * 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_key = f"{message.guild.id}-{message.author.id}"

        if user_key in self.cooldowns:
            return

        self.cooldowns.add(user_key)

        user = db.get_user(user_key)

        xp_gain = random.randint(10, 25)
        user["xp"] += xp_gain
        user["coins"] += random.randint(1, 5)

        required = self.level_required_xp(user["level"])

        if user["xp"] >= required:
            user["xp"] -= required
            user["level"] += 1

            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached **Level {user['level']}**!",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)

        db.update_user(user_key, user)

        async def remove_cooldown():
            import asyncio
            await asyncio.sleep(60)
            self.cooldowns.discard(user_key)

        self.bot.loop.create_task(remove_cooldown())

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_key = f"{ctx.guild.id}-{member.id}"
        user = db.get_user(user_key)

        embed = discord.Embed(
            title=f"📊 {member.name}'s Rank",
            color=discord.Color.red()
        )
        embed.add_field(name="Level", value=user["level"], inline=True)
        embed.add_field(name="XP", value=user["xp"], inline=True)
        embed.add_field(name="Coins", value=user["coins"], inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command()
    async def daily(self, ctx):
        user_key = f"{ctx.guild.id}-{ctx.author.id}"
        user = db.get_user(user_key)

        reward = random.randint(100, 250)
        user["coins"] += reward

        db.update_user(user_key, user)

        await ctx.reply(f"🎁 You claimed **{reward} coins** daily reward!")

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_key = f"{ctx.guild.id}-{member.id}"
        user = db.get_user(user_key)

        await ctx.reply(f"🪙 {member.mention} has **{user['coins']} coins**.")

    @commands.command()
    async def leaderboard(self, ctx):
        data = db.load()

        users = data.get("users", {})

        sorted_users = sorted(
            users.items(),
            key=lambda item: item[1].get("level", 1),
            reverse=True
        )[:10]

        if not sorted_users:
            await ctx.reply("No leaderboard data yet.")
            return

        description = ""

        for index, (user_id, info) in enumerate(sorted_users, start=1):
            description += f"**#{index}** `{user_id}` — Level {info.get('level', 1)} | XP {info.get('xp', 0)}\n"

        embed = discord.Embed(
            title="🏆 ZELROVA Leaderboard",
            description=description,
            color=discord.Color.red()
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def shop(self, ctx):
        embed = discord.Embed(
            title="🛒 ZELROVA Shop",
            description="Coming soon: roles, badges, perks and premium items.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Levels(bot))