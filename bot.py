import asyncio
import os
import requests
import discord
from discord.ext import commands, tasks

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
    "cogs.owner",
    "cogs.onboarding",
    "cogs.music"
]


DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5000")


def calculate_total_members():
    return sum(guild.member_count or 0 for guild in bot.guilds)


def calculate_security_score():
    if not bot.guilds:
        return 0

    total_score = 0

    for guild in bot.guilds:
        server = db.get_server(guild.id)
        modules = server.get("modules", {})

        score = 0
        if modules.get("security"):
            score += 25
        if modules.get("automod"):
            score += 25
        if modules.get("moderation"):
            score += 20
        if modules.get("logs"):
            score += 15
        if modules.get("backup"):
            score += 15

        total_score += score

    return round(total_score / len(bot.guilds))


def sync_dashboard_state():
    try:
        payload = {
            "status": "Online",
            "latency": f"{round(bot.latency * 1000)}ms",
            "servers": len(bot.guilds),
            "users": calculate_total_members(),
            "commands": 0,
            "security_score": calculate_security_score()
        }

        requests.post(
            f"{DASHBOARD_URL}/api/bot-state/update",
            json=payload,
            timeout=5
        )

    except Exception:
        pass


@tasks.loop(minutes=2)
async def dashboard_sync_loop():
    sync_dashboard_state()


@bot.event
async def on_ready():
    print("====================================")
    print("ZELROVA is online!")
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

    db.update_bot_state(
        status="online",
        servers=len(bot.guilds),
        users=calculate_total_members()
    )

    for guild in bot.guilds:
        server = db.get_server(guild.id)
        server["server_name"] = guild.name
        server["server_id"] = str(guild.id)
        server["owner_id"] = str(guild.owner_id)
        server["member_count"] = guild.member_count or 0
        server["icon_url"] = guild.icon.url if guild.icon else None
        db.update_server(guild.id, server)

        print(f"Server detected: {guild.name} ({guild.id})")

    sync_dashboard_state()

    if not dashboard_sync_loop.is_running():
        dashboard_sync_loop.start()


@bot.event
async def on_guild_join(guild):
    server = db.get_server(guild.id)
    server["server_name"] = guild.name
    server["server_id"] = str(guild.id)
    server["owner_id"] = str(guild.owner_id)
    server["member_count"] = guild.member_count or 0
    server["icon_url"] = guild.icon.url if guild.icon else None
    server["bot_joined"] = True
    db.update_server(guild.id, server)

    db.add_log(guild.id, "system", f"ZELROVA joined server: {guild.name}")

    sync_dashboard_state()

    print(f"New server joined: {guild.name} ({guild.id})")


@bot.event
async def on_guild_remove(guild):
    data = db.load()
    guild_id = str(guild.id)

    if guild_id in data.get("servers", {}):
        data["servers"][guild_id]["bot_joined"] = False
        data["servers"][guild_id]["left_at"] = "Left server"
        db.save(data)

    sync_dashboard_state()

    print(f"Removed from server: {guild.name} ({guild.id})")


@bot.event
async def on_command(ctx):
    if ctx.guild:
        db.increment_stat(ctx.guild.id, "commands")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild:
        db.increment_stat(message.guild.id, "messages")

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("❌ Missing command argument.")
    elif isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("❌ Invalid command argument.")
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
    embed.add_field(name="Users", value=str(calculate_total_members()), inline=True)
    embed.add_field(name="Prefix", value=Config.PREFIX, inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Dashboard", value="Active", inline=True)

    embed.set_footer(text="ZELROVA Control Center")

    await ctx.reply(embed=embed)


@bot.command()
async def topservers(ctx):
    data = db.load()
    servers = data.get("servers", {})

    ranking = []

    for guild_id, info in servers.items():
        name = info.get("server_name", "Unknown Server")
        members = info.get("member_count", 0)
        stats = info.get("stats", {})
        commands = stats.get("commands", 0)
        tickets = stats.get("tickets", 0)
        warnings = stats.get("warnings", 0)

        trust_score = min(100, int((members / 100) + (commands / 50) + (tickets * 2) - warnings))

        ranking.append({
            "name": name,
            "members": members,
            "commands": commands,
            "trust_score": trust_score
        })

    ranking.sort(key=lambda x: (x["trust_score"], x["members"]), reverse=True)

    description = ""

    for index, server in enumerate(ranking[:10], start=1):
        description += (
            f"**#{index} {server['name']}**\n"
            f"👥 Members: `{server['members']}`\n"
            f"⚡ Commands: `{server['commands']}`\n"
            f"⭐ Trust Score: `{server['trust_score']}%`\n\n"
        )

    if not description:
        description = "No servers found yet."

    embed = discord.Embed(
        title="🏆 ZELROVA Top Trusted Servers",
        description=description,
        color=discord.Color.red()
    )

    await ctx.reply(embed=embed)

@bot.command(name="command", aliases=["commands", "help"])
async def command_list(ctx):
    embed = discord.Embed(
        title="📜 ZELROVA Bot Commands",
        description="One Bot. Everything You Need.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="⚡ Basic",
        value="`!ping`\n`!zelrova`\n`!command`\n`!topservers`",
        inline=False
    )

    embed.add_field(
        name="🛡 Moderation",
        value="`!warn @user reason`\n`!warnings @user`\n`!clearwarnings @user`\n`!kick @user reason`\n`!ban @user reason`\n`!unban user_id`\n`!timeout @user minutes reason`\n`!untimeout @user`\n`!clear amount`\n`!lock`\n`!unlock`\n`!slowmode seconds`\n`!nickname @user name`",
        inline=False
    )

    embed.add_field(
        name="🔐 Security / AutoMod",
        value="`!security`\n`!joinlock`\n`!joinunlock`\n`!lockdown`\n`!unlockdown`\n`!verification`\n`!automod`\n`!addbadword word`",
        inline=False
    )

    embed.add_field(
        name="🎫 Tickets",
        value="`!ticket reason`\n`!claim`\n`!close`\n`!add @user`\n`!remove @user`\n`!rename name`\n`!transcript`\n`!tickets`",
        inline=False
    )

    embed.add_field(
        name="📊 Levels / Economy",
        value="`!rank`\n`!leaderboard`\n`!balance`\n`!daily`\n`!shop`\n`!inventory`\n`!achievements`\n`!levels`",
        inline=False
    )

    embed.add_field(
        name="🧠 AI",
        value="`!ai question`\n`!translate language text`\n`!summarize text`\n`!codehelp question`\n`!animehelp anime`\n`!storyhelp idea`\n`!faq`\n`!aihelp`",
        inline=False
    )

    embed.add_field(
        name="👋 Onboarding / Music / Logs",
        value="`!onboarding`\n`!onboardinginfo`\n`!music`\n`!joinvc`\n`!leavevc`\n`!logs`\n`!logstats`\n`!exportlogs`",
        inline=False
    )

    embed.add_field(
        name="👑 Owner Only",
        value="`!owner`\n`!setstatus`\n`!broadcast`\n`!servers`\n`!reloadcog`\n`!syncstate`\n`!maintenance`\n`!devmode`\n`!premiumserver`\n`!databaseinfo`",
        inline=False
    )

    embed.set_footer(text="ZELROVA Bot • One Bot. Everything You Need.")
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