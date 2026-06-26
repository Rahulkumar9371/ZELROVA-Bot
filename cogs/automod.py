import re
import time
import datetime
import discord
from discord.ext import commands

from database import db


BAD_WORDS = [
    "badword1",
    "badword2",
    "badword3"
]

INVITE_REGEX = r"(discord\.gg\/|discord\.com\/invite\/|discordapp\.com\/invite\/)"
URL_REGEX = r"(https?:\/\/[^\s]+)"

SCAM_WORDS = [
    "free nitro",
    "nitro gift",
    "claim nitro",
    "steam gift",
    "free robux",
    "airdrop",
    "crypto giveaway"
]

MAX_MENTIONS = 5
MAX_EMOJIS = 12
MAX_CAPS_PERCENT = 75
DUPLICATE_WINDOW = 10
FLOOD_WINDOW = 6
FLOOD_LIMIT = 5


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_messages = {}
        self.message_times = {}

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def automod_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "automod", f"{title} | {description}")
        except Exception:
            pass

        channel = discord.utils.get(guild.text_channels, name="zelrova-logs")

        if channel:
            await channel.send(embed=self.embed(title, description))

    async def punish(self, message, reason):
        try:
            await message.delete()
        except Exception:
            pass

        try:
            await message.channel.send(
                f"🤖 {message.author.mention} AutoMod: **{reason}**",
                delete_after=6
            )
        except Exception:
            pass

        await self.automod_log(
            message.guild,
            "🤖 AutoMod Action",
            f"User: {message.author} (`{message.author.id}`)\nChannel: {message.channel.mention}\nReason: {reason}"
        )

    def module_enabled(self, guild_id, module_name):
        try:
            server = db.get_server(guild_id)
            return server.get("modules", {}).get("automod", True) and server.get("automod", {}).get(module_name, True)
        except Exception:
            return True

    def count_emojis(self, text):
        return sum(1 for char in text if ord(char) > 10000)

    def caps_percent(self, text):
        letters = [c for c in text if c.isalpha()]

        if len(letters) < 10:
            return 0

        caps = sum(1 for c in letters if c.isupper())
        return (caps / len(letters)) * 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            return

        if message.author.guild_permissions.manage_messages:
            return

        content = message.content
        lower = content.lower()

        guild_id = message.guild.id
        user_id = message.author.id
        now = time.time()

        if self.module_enabled(guild_id, "bad_words"):
            for word in BAD_WORDS:
                if word and word.lower() in lower:
                    await self.punish(message, "Bad word detected")
                    return

        if self.module_enabled(guild_id, "invite_links"):
            if re.search(INVITE_REGEX, lower):
                await self.punish(message, "Discord invite link blocked")
                return

        if self.module_enabled(guild_id, "scam_links"):
            if re.search(URL_REGEX, lower):
                if any(word in lower for word in SCAM_WORDS):
                    await self.punish(message, "Possible scam link detected")
                    return

        if self.module_enabled(guild_id, "mention_spam"):
            if len(message.mentions) >= MAX_MENTIONS:
                await self.punish(message, "Mention spam detected")
                return

        if self.module_enabled(guild_id, "emoji_spam"):
            if self.count_emojis(content) >= MAX_EMOJIS:
                await self.punish(message, "Emoji spam detected")
                return

        if self.module_enabled(guild_id, "caps_spam"):
            if self.caps_percent(content) >= MAX_CAPS_PERCENT:
                await self.punish(message, "Caps spam detected")
                return

        if self.module_enabled(guild_id, "duplicate_messages"):
            key = f"{guild_id}-{user_id}"
            old = self.last_messages.get(key)

            if old:
                old_content, old_time = old
                if old_content == content and now - old_time <= DUPLICATE_WINDOW:
                    await self.punish(message, "Duplicate message detected")
                    return

            self.last_messages[key] = (content, now)

        if self.module_enabled(guild_id, "spam_protection"):
            key = f"{guild_id}-{user_id}"
            self.message_times.setdefault(key, [])
            self.message_times[key].append(now)

            self.message_times[key] = [
                t for t in self.message_times[key]
                if now - t <= FLOOD_WINDOW
            ]

            if len(self.message_times[key]) >= FLOOD_LIMIT:
                await self.punish(message, "Flood spam detected")
                return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addbadword(self, ctx, *, word):
        if word.lower() not in BAD_WORDS:
            BAD_WORDS.append(word.lower())

        await ctx.reply(
            embed=self.embed(
                "✅ Bad Word Added",
                f"`{word}` added to AutoMod filter."
            )
        )

    @commands.command()
    async def automod(self, ctx):
        embed = self.embed(
            "🤖 ZELROVA AutoMod",
            "Automatic moderation protection status."
        )

        embed.add_field(name="Bad Words", value="🟢 Active", inline=True)
        embed.add_field(name="Spam", value="🟢 Active", inline=True)
        embed.add_field(name="Invite Links", value="🟢 Active", inline=True)
        embed.add_field(name="Scam Links", value="🟢 Active", inline=True)
        embed.add_field(name="Mention Spam", value="🟢 Active", inline=True)
        embed.add_field(name="Emoji Spam", value="🟢 Active", inline=True)
        embed.add_field(name="Caps Spam", value="🟢 Active", inline=True)
        embed.add_field(name="Duplicate Messages", value="🟢 Active", inline=True)
        embed.add_field(name="Flood Detection", value="🟢 Active", inline=True)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))