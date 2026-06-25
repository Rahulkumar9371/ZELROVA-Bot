import discord
from discord.ext import commands


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @commands.command()
    async def ai(self, ctx, *, question=None):
        if not question:
            await ctx.reply("🧠 Ask something like: `!ai explain Discord bots`")
            return

        response = (
            "🧠 **ZELROVA AI Response**\n\n"
            "AI backend placeholder active.\n"
            "Later we will connect this with a real AI system.\n\n"
            f"**Your Question:** {question}"
        )

        await ctx.reply(response)

    @commands.command()
    async def translate(self, ctx, language=None, *, text=None):
        if not language or not text:
            await ctx.reply("🌍 Use: `!translate english नमस्ते`")
            return

        await ctx.reply(
            f"🌍 **AI Translate Placeholder**\n\n"
            f"Target Language: `{language}`\n"
            f"Text: {text}"
        )

    @commands.command()
    async def summarize(self, ctx, *, text=None):
        if not text:
            await ctx.reply("📄 Use: `!summarize your long text here`")
            return

        short = text[:180] + "..." if len(text) > 180 else text

        await ctx.reply(f"📄 **Summary:** {short}")

    @commands.command()
    async def codehelp(self, ctx, *, question=None):
        if not question:
            await ctx.reply("💻 Use: `!codehelp your coding question`")
            return

        await ctx.reply(
            f"💻 **Coding Helper Active**\n\n"
            f"Question: {question}\n\n"
            f"Real coding AI will be connected later."
        )

    @commands.command()
    async def animehelp(self, ctx, *, anime=None):
        if not anime:
            await ctx.reply("🎌 Use: `!animehelp anime name`")
            return

        await ctx.reply(
            f"🎌 **Anime Helper Active**\n\n"
            f"Anime: {anime}\n"
            f"Later this will support anime info, characters, manga and recommendations."
        )

    @commands.command()
    async def storyhelp(self, ctx, *, idea=None):
        if not idea:
            await ctx.reply("✍️ Use: `!storyhelp your story idea`")
            return

        await ctx.reply(
            f"✍️ **Story Helper Active**\n\n"
            f"Idea: {idea}\n\n"
            f"Later this will help with plot, characters, arcs and worldbuilding."
        )


async def setup(bot):
    await bot.add_cog(AI(bot))