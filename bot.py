import asyncio
import os
from datetime import datetime, timezone

import requests
import discord
from discord import app_commands
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


DASHBOARD_URL = Config.DASHBOARD_URL.rstrip("/")


def safe_post(endpoint, payload):
    try:
        res = requests.post(
            f"{DASHBOARD_URL}{endpoint}",
            json=payload,
            timeout=8
        )
        return res.status_code, res.text
    except Exception as e:
        return 0, str(e)


def safe_get(endpoint):
    try:
        res = requests.get(
            f"{DASHBOARD_URL}{endpoint}",
            timeout=8
        )
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def get_server_stats(guild_id):
    server = db.get_server(guild_id)
    stats = server.get("stats", {})

    return {
        "commands": int(stats.get("commands", 0) or 0),
        "tickets": int(stats.get("tickets", 0) or 0),
        "warnings": int(stats.get("warnings", 0) or 0),
        "messages": int(stats.get("messages", 0) or 0),
        "joins": int(stats.get("joins", 0) or 0),
        "bans": int(stats.get("bans", 0) or 0),
        "kicks": int(stats.get("kicks", 0) or 0)
    }


def calculate_trust_score(guild, stats):
    members = guild.member_count or 0

    score = 50
    score += min(20, members // 50)
    score += min(15, stats["commands"] // 20)
    score += min(10, stats["tickets"] * 2)
    score -= min(25, stats["warnings"])

    return max(0, min(100, int(score)))


def calculate_activity_score(stats):
    score = 20
    score += min(35, stats["messages"] // 50)
    score += min(30, stats["commands"] // 10)
    score += min(15, stats["tickets"] * 2)

    return max(0, min(100, int(score)))


async def get_owner_name(guild):
    try:
        owner = guild.owner or await bot.fetch_user(guild.owner_id)
        return str(owner)
    except Exception:
        return str(guild.owner_id)


def calculate_global_security_score():
    if not bot.guilds:
        return 0

    total = 0

    for guild in bot.guilds:
        server = db.get_server(guild.id)
        modules = server.get("modules", {})

        score = 0
        if modules.get("security", True):
            score += 25
        if modules.get("automod", True):
            score += 25
        if modules.get("moderation", True):
            score += 20
        if modules.get("logs", True):
            score += 15
        if modules.get("backup", True):
            score += 15

        total += min(100, score)

    return round(total / len(bot.guilds))


async def build_live_server_payload():
    servers = []

    for guild in bot.guilds:
        db.mark_server_live(guild)
        stats = get_server_stats(guild.id)
        owner_name = await get_owner_name(guild)

        joined_at = "Unknown"
        if guild.me and guild.me.joined_at:
            joined_at = guild.me.joined_at.strftime("%Y-%m-%d %H:%M:%S")

        servers.append({
            "id": str(guild.id),
            "name": guild.name,
            "owner_id": str(guild.owner_id),
            "owner_name": owner_name,
            "members": guild.member_count or 0,
            "icon": guild.icon.url if guild.icon else None,
            "joined_at": joined_at,
            "commands": stats["commands"],
            "tickets": stats["tickets"],
            "warnings": stats["warnings"],
            "messages": stats["messages"],
            "trust_score": calculate_trust_score(guild, stats),
            "activity_score": calculate_activity_score(stats),
            "online": True,
            "premium": db.is_premium_server(guild.id),
            "bot_joined": True
        })

    return {
        "servers": servers,
        "users": sum(s["members"] for s in servers),
        "commands": sum(s["commands"] for s in servers),
        "latency": f"{round(bot.latency * 1000)}ms",
        "security_score": calculate_global_security_score(),
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }


async def sync_live_dashboard():
    payload = await build_live_server_payload()

    db.update_bot_state(
        status="online",
        servers=len(payload["servers"]),
        users=payload["users"],
        latency=payload["latency"]
    )

    status, text = safe_post("/api/bot/live-sync", payload)

    if status == 200:
        print(f"[LIVE SYNC] Synced {len(payload['servers'])} servers.")
    else:
        print(f"[LIVE SYNC ERROR] {status} {text}")


def get_music_cog():
    return bot.get_cog("Music")


async def execute_music_action(action, payload):
    music = get_music_cog()

    if not music:
        return "Music cog not loaded."

    try:
        if action == "music_pause":
            result = await music.dashboard_pause()
        elif action == "music_resume":
            result = await music.dashboard_resume()
        elif action == "music_skip":
            result = await music.dashboard_skip()
        elif action == "music_stop":
            result = await music.dashboard_stop()
        elif action == "music_volume":
            result = await music.dashboard_volume(int(payload.get("value", 75)))
        elif action == "music_loop":
            result = await music.dashboard_loop()
        elif action == "music_shuffle":
            result = await music.dashboard_shuffle()
        else:
            result = f"Unsupported music action: {action}"

        return result

    except Exception as e:
        return f"Music action failed: {e}"


async def execute_owner_action(action_item):
    action_id = action_item.get("id")
    action = action_item.get("action")
    payload = action_item.get("payload", {})

    result = "completed"

    try:
        if action == "leave_server":
            server_id = int(payload.get("server_id"))
            guild = bot.get_guild(server_id)

            if not guild:
                result = "Server not found or bot already left."
            else:
                name = guild.name
                await guild.leave()
                db.mark_server_removed(server_id)
                result = f"ZELROVA left server: {name}"

        elif action.startswith("music_"):
            result = await execute_music_action(action, payload)

        elif action == "Global Broadcast":
            message = payload.get("message") or "ZELROVA Broadcast"
            sent = 0

            for guild in bot.guilds:
                channel = guild.system_channel
                if channel:
                    try:
                        await channel.send(f"📢 **ZELROVA Broadcast**\n\n{message}")
                        sent += 1
                    except Exception:
                        pass

            result = f"Broadcast sent to {sent} servers."

        elif action == "Bot Status Control":
            await bot.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=Config.MISSION
                )
            )
            result = "Bot status refreshed."

        elif action == "Maintenance Mode":
            data = db.load()
            current = data["bot"].get("maintenance", False)
            data["bot"]["maintenance"] = not current
            db.save(data)
            result = f"Maintenance mode: {not current}"

        elif action == "Developer Mode":
            data = db.load()
            current = data["bot"].get("developer_mode", False)
            data["bot"]["developer_mode"] = not current
            db.save(data)
            result = f"Developer mode: {not current}"

        elif action == "sync_modules":
            result = "Modules synced."

        elif action == "sync_automod":
            result = "AutoMod synced."

        else:
            result = f"Unknown owner action: {action}"

    except Exception as e:
        result = f"Action failed: {e}"

    safe_post("/api/owner/action-complete", {
        "action_id": action_id,
        "result": result
    })

    print(f"[OWNER ACTION] {action} -> {result}")
    await sync_live_dashboard()


@tasks.loop(seconds=8)
async def owner_action_loop():
    actions = safe_get("/api/owner/actions")

    if not actions:
        return

    pending = actions.get("pending", [])

    for action_item in pending[:5]:
        await execute_owner_action(action_item)


@tasks.loop(seconds=20)
async def live_sync_loop():
    await sync_live_dashboard()


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
            name=Config.MISSION
        ),
        status=discord.Status.online
    )

    for guild in bot.guilds:
        db.mark_server_live(guild)
        print(f"Server detected: {guild.name} ({guild.id})")

    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Slash sync failed: {e}")

    await sync_live_dashboard()

    if not live_sync_loop.is_running():
        live_sync_loop.start()

    if not owner_action_loop.is_running():
        owner_action_loop.start()


@bot.event
async def on_guild_join(guild):
    db.mark_server_live(guild)
    db.add_log(guild.id, "system", f"ZELROVA joined server: {guild.name}")
    print(f"New server joined: {guild.name} ({guild.id})")
    await sync_live_dashboard()


@bot.event
async def on_guild_remove(guild):
    db.mark_server_removed(guild.id)
    print(f"Removed from server: {guild.name} ({guild.id})")
    await sync_live_dashboard()


@bot.event
async def on_member_join(member):
    if member.guild:
        db.increment_stat(member.guild.id, "joins")
        db.mark_server_live(member.guild)
        await sync_live_dashboard()


@bot.event
async def on_member_remove(member):
    if member.guild:
        db.mark_server_live(member.guild)
        await sync_live_dashboard()


@bot.event
async def on_command(ctx):
    if ctx.guild:
        db.increment_stat(ctx.guild.id, "commands")
        await sync_live_dashboard()


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


@bot.tree.command(name="z", description="Show all ZELROVA slash commands")
async def z_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 ZELROVA Commands",
        description=Config.MISSION,
        color=discord.Color.red()
    )

    embed.add_field(
        name="🎵 Music",
        value=(
            "`/zplay` `/zsearch` `/zstop` `/zpause` `/zresume`\n"
            "`/zskip` `/zqueue` `/zvolume` `/zloop` `/zshuffle` `/znowplaying` `/zplayfile`"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡 Moderation",
        value="`/zcommand` shows all prefix and slash commands. Moderation commands are also available with `z!` prefix.",
        inline=False
    )

    embed.add_field(
        name="🌐 Dashboard",
        value="Use dashboard for live server control, music control, owner panel, backups and analytics.",
        inline=False
    )

    embed.set_footer(text="ZELROVA Bot • /z command center")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="zcommand", description="Show full ZELROVA command list")
async def z_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 ZELROVA Full Command List",
        description="Slash-first command system.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="🎵 Music",
        value="/zplay, /zsearch, /zstop, /zpause, /zresume, /zskip, /zqueue, /zvolume, /zloop, /zshuffle, /znowplaying, /zplayfile",
        inline=False
    )

    embed.add_field(
        name="⚙ Prefix Backup",
        value="Some older commands still use `z!` prefix for moderation, tickets, levels and owner tools while we migrate them to slash.",
        inline=False
    )

    await interaction.response.send_message(embed=embed)


@bot.command()
async def ping(ctx):
    await ctx.reply(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")


@bot.command()
async def zelrova(ctx):
    embed = discord.Embed(
        title="ZELROVA Bot",
        description=Config.MISSION,
        color=discord.Color.red()
    )

    embed.add_field(name="Version", value=Config.VERSION, inline=True)
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Users", value=str(sum(g.member_count or 0 for g in bot.guilds)), inline=True)
    embed.add_field(name="Prefix", value=Config.PREFIX, inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Dashboard", value="Live", inline=True)

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