import asyncio
import io
import datetime
import discord
from discord.ext import commands

from database import db


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=discord.Color.red()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

    async def ticket_log(self, guild, title, description):
        try:
            db.add_log(guild.id, "tickets", f"{title} | {description}")
        except Exception:
            pass

        channel = discord.utils.get(guild.text_channels, name="zelrova-logs")

        if channel:
            await channel.send(embed=self.embed(title, description))

    @commands.command()
    async def ticket(self, ctx, *, reason="Support Request"):
        server = db.get_server(ctx.guild.id)
        ticket_settings = server.get("tickets", {})

        if not ticket_settings.get("enabled", True):
            await ctx.reply("❌ Ticket system disabled hai.")
            return

        category_name = ticket_settings.get("category_name", "Tickets")

        category = discord.utils.get(ctx.guild.categories, name=category_name)

        if category is None:
            category = await ctx.guild.create_category(category_name)

        existing = None

        for channel in category.text_channels:
            if channel.name == f"ticket-{ctx.author.id}":
                existing = channel
                break

        if existing:
            await ctx.reply(f"❌ Tumhara ticket already open hai: {existing.mention}")
            return

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        staff_role_id = server.get("roles", {}).get("staff")

        if staff_role_id:
            staff_role = ctx.guild.get_role(int(staff_role_id))
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.id}",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {ctx.author}"
        )

        db.create_ticket(ctx.guild.id, channel.id, ctx.author.id)

        embed = self.embed(
            "🎫 Ticket Created",
            (
                f"Welcome {ctx.author.mention}!\n\n"
                f"**Reason:** {reason}\n\n"
                "Support team will help you soon.\n\n"
                "**Commands:**\n"
                "`!claim` — Staff claim ticket\n"
                "`!add @user` — Add user\n"
                "`!remove @user` — Remove user\n"
                "`!transcript` — Save transcript\n"
                "`!close` — Close ticket"
            )
        )

        await channel.send(embed=embed)

        await ctx.reply(f"✅ Ticket created: {channel.mention}")

        await self.ticket_log(
            ctx.guild,
            "Ticket Created",
            f"Ticket {channel.mention} created by {ctx.author}. Reason: {reason}"
        )

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.reply("❌ Ye ticket channel nahi lag raha.")
            return

        await ctx.reply("🗑 Ticket 5 seconds mein close hoga.")
        db.close_ticket(ctx.guild.id, ctx.channel.id)

        await self.ticket_log(
            ctx.guild,
            "Ticket Closed",
            f"{ctx.channel.name} closed by {ctx.author}"
        )

        await asyncio.sleep(5)
        await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def claim(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.reply("❌ Ye ticket channel nahi lag raha.")
            return

        db.claim_ticket(ctx.guild.id, ctx.channel.id, ctx.author.id)

        await ctx.reply(
            embed=self.embed(
                "👮 Ticket Claimed",
                f"{ctx.author.mention} claimed this ticket."
            )
        )

        await self.ticket_log(
            ctx.guild,
            "Ticket Claimed",
            f"{ctx.channel.name} claimed by {ctx.author}"
        )

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx, *, name):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.reply("❌ Ye ticket channel nahi lag raha.")
            return

        safe_name = name.lower().replace(" ", "-")[:90]
        await ctx.channel.edit(name=safe_name)

        await ctx.reply(f"✅ Ticket renamed to **{safe_name}**")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def add(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(
            member,
            read_messages=True,
            send_messages=True,
            attach_files=True
        )

        await ctx.reply(f"✅ {member.mention} added to this ticket.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.reply(f"❌ {member.mention} removed from this ticket.")

    @commands.command()
    async def transcript(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.reply("❌ Ye ticket channel nahi lag raha.")
            return

        messages = []

        async for msg in ctx.channel.history(limit=None, oldest_first=True):
            content = msg.content if msg.content else ""
            attachments = " ".join([a.url for a in msg.attachments])
            messages.append(
                f"[{msg.created_at}] {msg.author} ({msg.author.id}): {content} {attachments}"
            )

        transcript_text = "\n".join(messages) or "No messages found."
        file_data = io.BytesIO(transcript_text.encode("utf-8"))

        file = discord.File(file_data, filename=f"{ctx.channel.name}-transcript.txt")

        await ctx.reply("📄 Ticket transcript generated.", file=file)

        await self.ticket_log(
            ctx.guild,
            "Transcript Generated",
            f"Transcript generated for {ctx.channel.name} by {ctx.author}"
        )

    @commands.command()
    async def tickets(self, ctx):
        embed = self.embed(
            "🎫 ZELROVA Ticket System",
            (
                "`!ticket reason` — Create ticket\n"
                "`!claim` — Claim ticket\n"
                "`!close` — Close ticket\n"
                "`!add @user` — Add user\n"
                "`!remove @user` — Remove user\n"
                "`!rename name` — Rename ticket\n"
                "`!transcript` — Generate transcript"
            )
        )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))