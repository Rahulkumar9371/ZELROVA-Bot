import asyncio
import io
import discord
from discord.ext import commands


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @commands.command()
    async def ticket(self, ctx):
        category = discord.utils.get(ctx.guild.categories, name="Tickets")

        if category is None:
            category = await ctx.guild.create_category("Tickets")

        existing = discord.utils.get(
            ctx.guild.text_channels,
            name=f"ticket-{ctx.author.name.lower()}"
        )

        if existing:
            await ctx.reply(f"❌ You already have a ticket: {existing.mention}")
            return

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            category=category,
            overwrites=overwrites
        )

        embed = self.embed(
            "🎫 Ticket Created",
            f"{ctx.author.mention}\n\nSupport team will help you soon.\n\nUse `!close` to close this ticket."
        )

        await channel.send(embed=embed)
        await ctx.reply(f"✅ Ticket created: {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx):
        await ctx.reply("🗑 Ticket will close in **5 seconds**.")
        await asyncio.sleep(5)
        await ctx.channel.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def claim(self, ctx):
        await ctx.reply(embed=self.embed(
            "👮 Ticket Claimed",
            f"{ctx.author.mention} claimed this ticket."
        ))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx, *, name):
        await ctx.channel.edit(name=name)
        await ctx.reply(f"✅ Ticket renamed to **{name}**")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def add(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.reply(f"✅ {member.mention} added to ticket.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.reply(f"❌ {member.mention} removed from ticket.")

    @commands.command()
    async def transcript(self, ctx):
        messages = []

        async for msg in ctx.channel.history(limit=None, oldest_first=True):
            messages.append(f"[{msg.created_at}] {msg.author}: {msg.content}")

        transcript_text = "\n".join(messages) or "No messages found."
        file_data = io.BytesIO(transcript_text.encode("utf-8"))

        file = discord.File(file_data, filename="transcript.txt")

        await ctx.reply("📄 Ticket transcript generated.", file=file)

    @commands.command()
    async def tickets(self, ctx):
        embed = discord.Embed(
            title="🎫 ZELROVA Ticket System",
            description="Ticket system is active.",
            color=discord.Color.red()
        )

        embed.add_field(name="Create", value="`!ticket`", inline=False)
        embed.add_field(name="Close", value="`!close`", inline=False)
        embed.add_field(name="Claim", value="`!claim`", inline=False)
        embed.add_field(name="Transcript", value="`!transcript`", inline=False)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))