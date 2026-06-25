import re
import discord
from discord.ext import commands

# ------------------------------
# CONFIG
# ------------------------------

BAD_WORDS = [
    "badword1",
    "badword2",
    "badword3"
]

INVITE_PATTERN = r"(discord\.gg\/|discord\.com\/invite\/)"
LINK_PATTERN = r"(https?:\/\/[^\s]+)"

MAX_CAPS_PERCENT = 70
MAX_EMOJIS = 10
MAX_MENTIONS = 5
MAX_MESSAGE_LENGTH = 2000


class AutoMod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.last_messages = {}

    # ------------------------------
    # MESSAGE LISTENER
    # ------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.lower()

        # ==========================
        # BAD WORD FILTER
        # ==========================

        for word in BAD_WORDS:

            if word in content:

                await message.delete()

                await message.channel.send(
                    f"⚠️ {message.author.mention} inappropriate language is not allowed.",
                    delete_after=5
                )

                return

        # ==========================
        # DISCORD INVITE
        # ==========================

        if re.search(INVITE_PATTERN, content):

            await message.delete()

            await message.channel.send(
                f"🚫 {message.author.mention} Discord invite links are blocked.",
                delete_after=5
            )

            return

        # ==========================
        # SCAM LINK
        # ==========================

        if re.search(LINK_PATTERN, content):

            suspicious = [
                "nitro",
                "gift",
                "free",
                "steam",
                "claim"
            ]

            for word in suspicious:

                if word in content:

                    await message.delete()

                    await message.channel.send(
                        f"🚫 Possible scam link removed.",
                        delete_after=5
                    )

                    return

        # ==========================
        # CAPS FILTER
        # ==========================

        letters = [c for c in message.content if c.isalpha()]

        if len(letters) > 8:

            caps = sum(1 for c in letters if c.isupper())

            percent = (caps / len(letters)) * 100

            if percent >= MAX_CAPS_PERCENT:

                await message.delete()

                await message.channel.send(
                    f"🔠 Too many capital letters.",
                    delete_after=5
                )

                return

        # ==========================
        # MENTION SPAM
        # ==========================

        if len(message.mentions) >= MAX_MENTIONS:

            await message.delete()

            await message.channel.send(
                f"📢 Mention spam detected.",
                delete_after=5
            )

            return

        # ==========================
        # DUPLICATE MESSAGE
        # ==========================

        user_id = message.author.id

        if user_id in self.last_messages:

            if self.last_messages[user_id] == message.content:

                await message.delete()

                await message.channel.send(
                    f"♻️ Duplicate messages are not allowed.",
                    delete_after=5
                )

                return

        self.last_messages[user_id] = message.content

        # ==========================
        # EMOJI SPAM
        # ==========================

        emoji_count = sum(
            1 for c in message.content
            if ord(c) > 10000
        )

        if emoji_count >= MAX_EMOJIS:

            await message.delete()

            await message.channel.send(
                f"😂 Emoji spam detected.",
                delete_after=5
            )

            return

        # ==========================
        # VERY LONG MESSAGE
        # ==========================

        if len(message.content) >= MAX_MESSAGE_LENGTH:

            await message.delete()

            await message.channel.send(
                f"📄 Message too long.",
                delete_after=5
            )

            return

    # ------------------------------
    # STATUS
    # ------------------------------

    @commands.command()
    async def automod(self, ctx):

        embed = discord.Embed(

            title="🤖 AutoMod Status",

            color=discord.Color.red()

        )

        embed.add_field(
            name="Bad Words",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Invite Filter",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Scam Filter",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Caps Filter",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Emoji Spam",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Mention Spam",
            value="🟢 Enabled",
            inline=False
        )

        embed.add_field(
            name="Duplicate Messages",
            value="🟢 Enabled",
            inline=False
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))