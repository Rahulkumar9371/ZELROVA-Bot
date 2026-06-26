import discord
from discord.ext import commands


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @commands.command()
    async def music(self, ctx):
        embed = self.embed(
            "🎵 ZELROVA Music System",
            (
                "Music system foundation is active.\n\n"
                "**Available now:**\n"
                "`!joinvc` — Bot joins your voice channel\n"
                "`!leavevc` — Bot leaves voice channel\n"
                "`!music` — Show music status\n\n"
                "**Coming next:**\n"
                "Play, pause, resume, stop, queue, radio and playlist."
            )
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def joinvc(self, ctx):
        if not ctx.author.voice:
            await ctx.reply("❌ Join a voice channel first.")
            return

        channel = ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.reply(f"✅ Joined voice channel: **{channel.name}**")

    @commands.command()
    async def leavevc(self, ctx):
        if not ctx.voice_client:
            await ctx.reply("❌ I am not in a voice channel.")
            return

        await ctx.voice_client.disconnect()
        await ctx.reply("✅ Left voice channel.")

    @commands.command()
    async def play(self, ctx, *, query=None):
        if not query:
            await ctx.reply("🎵 Use: `!play song name or url`")
            return

        await ctx.reply(
            "🎵 Music play placeholder active.\n"
            "Real YouTube/streaming player will be connected in next music upgrade."
        )

    @commands.command()
    async def pause(self, ctx):
        await ctx.reply("⏸ Pause placeholder active.")

    @commands.command()
    async def resume(self, ctx):
        await ctx.reply("▶ Resume placeholder active.")

    @commands.command()
    async def stop(self, ctx):
        await ctx.reply("⏹ Stop placeholder active.")

    @commands.command()
    async def queue(self, ctx):
        await ctx.reply("📜 Queue placeholder active.")


async def setup(bot):
    await bot.add_cog(Music(bot))