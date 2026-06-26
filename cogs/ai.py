import datetime
import discord
from discord.ext import commands

from database import db


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def ai_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "ai", f"{title} | {description}")
        except Exception:
            pass

    def ai_reply(self, prompt):
        prompt = prompt.lower()

        if "discord" in prompt or "bot" in prompt:
            return (
                "ZELROVA AI: Discord bot banane ke liye tumhe Python, discord.py, "
                "events, commands, intents aur hosting samajhni hogi."
            )

        if "anime" in prompt:
            return (
                "ZELROVA AI: Anime ke liye story, characters, emotion, mystery aur "
                "worldbuilding sabse important hote hain."
            )

        if "code" in prompt or "python" in prompt:
            return (
                "ZELROVA AI: Coding mein pehle logic samjho, phir syntax. "
                "Python projects se practice best hoti hai."
            )

        if "story" in prompt:
            return (
                "ZELROVA AI: Strong story ke liye theme, conflict, characters, "
                "world rules aur emotional payoff zaroori hota hai."
            )

        return (
            "ZELROVA AI placeholder active hai. Real AI API baad mein connect hogi. "
            "Abhi ye smart rule-based replies de raha hai."
        )

    @commands.command()
    async def ai(self, ctx, *, question=None):
        if not question:
            await ctx.reply("🧠 Use: `!ai your question`")
            return

        server = db.get_server(ctx.guild.id)

        if not server.get("modules", {}).get("ai", True):
            await ctx.reply("❌ AI module disabled hai.")
            return

        response = self.ai_reply(question)

        await ctx.reply(
            embed=self.embed(
                "🧠 ZELROVA AI",
                f"**Question:** {question}\n\n**Answer:** {response}"
            )
        )

        await self.ai_log(
            ctx.guild,
            "AI Chat",
            f"{ctx.author} asked: {question}"
        )

    @commands.command()
    async def translate(self, ctx, language=None, *, text=None):
        if not language or not text:
            await ctx.reply("🌍 Use: `!translate english नमस्ते`")
            return

        await ctx.reply(
            embed=self.embed(
                "🌍 AI Translate",
                (
                    f"**Target Language:** {language}\n"
                    f"**Original Text:** {text}\n\n"
                    "Real translation API future upgrade mein connect hogi."
                )
            )
        )

    @commands.command()
    async def summarize(self, ctx, *, text=None):
        if not text:
            await ctx.reply("📄 Use: `!summarize long text`")
            return

        short = text[:250] + "..." if len(text) > 250 else text

        await ctx.reply(
            embed=self.embed(
                "📄 AI Summary",
                short
            )
        )

    @commands.command()
    async def codehelp(self, ctx, *, question=None):
        if not question:
            await ctx.reply("💻 Use: `!codehelp your coding question`")
            return

        await ctx.reply(
            embed=self.embed(
                "💻 AI Coding Helper",
                (
                    f"**Question:** {question}\n\n"
                    "Step 1: Error ko dhyan se read karo.\n"
                    "Step 2: File name aur line number check karo.\n"
                    "Step 3: Small test run karo.\n"
                    "Step 4: Fix ko save karke dobara run karo."
                )
            )
        )

    @commands.command()
    async def animehelp(self, ctx, *, anime=None):
        if not anime:
            await ctx.reply("🎌 Use: `!animehelp anime name`")
            return

        await ctx.reply(
            embed=self.embed(
                "🎌 AI Anime Helper",
                (
                    f"**Anime:** {anime}\n\n"
                    "Spoiler-free mode recommended. Pehle anime dekho, phir manga/ending discussions check karo."
                )
            )
        )

    @commands.command()
    async def storyhelp(self, ctx, *, idea=None):
        if not idea:
            await ctx.reply("✍️ Use: `!storyhelp your idea`")
            return

        await ctx.reply(
            embed=self.embed(
                "✍️ AI Story Helper",
                (
                    f"**Idea:** {idea}\n\n"
                    "Strong story ke liye:\n"
                    "1. Main theme\n"
                    "2. Main conflict\n"
                    "3. Character goal\n"
                    "4. Mystery\n"
                    "5. Emotional payoff"
                )
            )
        )

    @commands.command()
    async def faq(self, ctx):
        await ctx.reply(
            embed=self.embed(
                "❓ ZELROVA AI FAQ",
                (
                    "**What is ZELROVA?**\n"
                    "All-in-one Discord bot platform.\n\n"
                    "**Features?**\n"
                    "Moderation, AutoMod, Tickets, Levels, AI, Logs, Dashboard, Onboarding.\n\n"
                    "**Dashboard?**\n"
                    "Use the ZELROVA website dashboard."
                )
            )
        )

    @commands.command()
    async def aihelp(self, ctx):
        await ctx.reply(
            embed=self.embed(
                "🧠 ZELROVA AI Commands",
                (
                    "`!ai question`\n"
                    "`!translate language text`\n"
                    "`!summarize text`\n"
                    "`!codehelp question`\n"
                    "`!animehelp anime name`\n"
                    "`!storyhelp idea`\n"
                    "`!faq`"
                )
            )
        )


async def setup(bot):
    await bot.add_cog(AI(bot))