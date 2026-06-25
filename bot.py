import asyncio
import discord
from discord.ext import commands

from config import Config
from database import db


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
intents.voice_states = True


bot = commands.Bot(
    command_prefix=Config.PREFIX,
    intents=intents,
    help_command=None
)


COGS = [
    "cogs.moderation",
    "cogs.security",
    "cogs.automod",
    "cogs.welcome",
    "cogs.tickets",
    "cogs.levels",
    "cogs.logs",
    "cogs.ai",
    "cogs.owner"
]


@bot.event
async def on_ready():
    print("====================================")
    print(f"{Config.BOT_NAME} is online!")
    print(f"Logged in as: {bot.user}")
    print(f"Servers: {len(bot.guilds)}")
    print("====================================")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="One Bot. Everything You Need."
        ),
        status=discord.Status.online
    )

    for guild in bot.guilds:
        db.get_server(guild.id)
        print(f"Server detected: {guild.name} ({guild.id})")


@bot.event
async def on_guild_join(guild):
    db.get_server(guild.id)
    print(f"New server joined: {guild.name} ({guild.id})")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("❌ Missing command argument.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.reply("❌ Something went wrong.")
        print(error)


@bot.command()
async def ping(ctx):
    await ctx.reply(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")


@bot.command()
async def zelrova(ctx):
    embed = discord.Embed(
        title="ZELROVA Bot",
        description="One Bot. Everything You Need.",
        color=discord.Color.red()
    )
    embed.add_field(name="Version", value=Config.VERSION, inline=True)
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Prefix", value=Config.PREFIX, inline=True)
    embed.set_footer(text="ZELROVA Control Center")
    await ctx.reply(embed=embed)


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"Loaded: {cog}")
        except Exception as e:
            print(f"Failed to load {cog}: {e}")


async def main():
    if not Config.DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN missing in .env file")
        return

    async with bot:
        await load_cogs()
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())